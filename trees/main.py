import chess
import pickle
import tqdm
import sys
import pandas as pd
import zss
import json
import chess.engine

class ChessTreeNode:
    def __init__(self, node, children, depth=0):
        fen, move = node
        board = chess.Board(fen)
        move = board.parse_uci(move)
        move_san = board.san(move)
        src, dst = move.from_square, move.to_square
        is_capture = str(board.piece_at(dst)).upper()

        board.push(move)
        self.move_attributes = {
            "san": move_san,
            "side": not board.turn,
            "piece": board.piece_at(dst).symbol().upper(),
            "depth": depth,
            "from_file": chess.square_file(src),
            "from_rank": chess.square_rank(src),
            "from_diagonal_1": chess.square_file(src) + chess.square_rank(src),
            "from_diagonal_2": chess.square_file(src) + (8 - chess.square_rank(src)),
            "to_file": chess.square_file(dst),
            "to_rank": chess.square_rank(dst),
            "to_diagonal_1": chess.square_file(dst) + chess.square_rank(dst),
            "to_diagonal_2": chess.square_file(dst) + (8 - chess.square_rank(dst)),
            "move_distance": chess.square_distance(src, dst),
            "capture": is_capture,
            "check": board.is_check(),
            "mate": board.is_checkmate(),
            "num_attacks": sum(1 for _, p 
                in board.piece_map(mask=int(board.attacks(dst))).items()
                if p.color == board.turn
            ),
            "num_defenses": sum(1 for _, p 
                in board.piece_map(mask=int(board.attacks(dst))).items()
                if p.color != board.turn
            ),
            "attacked_by_num": len(board.attackers(board.turn, dst)),
            "defended_by_num": len(board.attackers(not board.turn, dst)),
        }
        self.children = [ChessTreeNode(*c, depth=depth+1) for c in children]

    def flip_san(self, flip=True):
        # This purely has a cosmetic effect and is used for printing purposes only
        # Yes, it's hacky :(
        if not flip:
            return self
        self.move_attributes["san"] = "".join(
            str(9-int(s)) if s.isnumeric() else s for s in self.move_attributes["san"] 
        )
        return self

    def __str__(self):
        d = self.move_attributes["depth"]
        san = self.move_attributes["san"]
        num_info = "/".join(str(self.move_attributes[x]) for x in 
            ["num_attacks", "num_defenses", "attacked_by_num", "defended_by_num"])
        return ("  " * d) + san + f" {num_info}\n" + "".join(map(str, self.children))

    @staticmethod
    def get_label(node):
        return node.move_attributes
    
    @staticmethod
    def get_children(node):
        return node.children
    
    @staticmethod
    def compare(a, b):
        depth_multiplier = {
            0: 4,
            1: 1,
            2: 0.5,
            3: 0.25,
            4: 0.1,
            5: 0.05,
        }


        # Adding/removing node
        # This depends on depth
        if a == "" or b == "":
            if a == "":
                a, b = b, a
            mult = depth_multiplier[a["depth"]]
            return 250 * mult

        # Compare sides
        if a["side"] != b["side"]:
            return 9999999
        
        if a["depth"] != b["depth"]:
            return 9999999

        mult = depth_multiplier[a["depth"]]

        # Compare 2 move attribute dictionaries.
        d = 0
        # Pieces
        p1 = a["piece"]
        p2 = b["piece"]
        if p1 == p2:
            pass
        elif {p1, p2} == {"R", "Q"}:
            d += 25
        elif {p1, p2} == {"B", "Q"}:
            d += 50
        else:
            d += 100
        
        # Squares
        if a["from_file"] != b["from_file"]:
            d += 3
        if a["from_rank"] != b["from_rank"]:
            d += 3
        if a["from_diagonal_1"] != b["from_diagonal_1"]:
            d += 3
        if a["from_diagonal_2"] != b["from_diagonal_2"]:
            d += 3

        if a["to_file"] != b["to_file"]:
            d += 3
        if a["to_rank"] != b["to_rank"]:
            d += 3
        if a["to_diagonal_1"] != b["to_diagonal_1"]:
            d += 3
        if a["to_diagonal_2"] != b["to_diagonal_2"]:
            d += 3

        d += abs(int(a["move_distance"]) - int(b["move_distance"]))


        if a["capture"] == b["capture"]:
            pass
        elif a["capture"] == "NONE" or b["capture"] == "NONE":
            # One is capture, the other isn't
            d += 50
        else:
            # Both captures, but different pieces
            d += 10

        if a["check"] != b["check"]:
            d += 50
 
        if a["mate"] != b["mate"]:
            d += 100
        
        d += 3 * abs(int(a["num_attacks"]) - int(b["num_attacks"]))
        d += 2 * abs(int(a["num_defenses"]) - int(b["num_defenses"]))
        d += 3 * abs(int(a["attacked_by_num"]) - int(b["attacked_by_num"]))
        d += 2 * abs(int(a["defended_by_num"]) - int(b["defended_by_num"]))

        return d * mult

def expand_tree(fen, move, engine, eval_threshold=100, depth=0):
    board = chess.Board(fen)
    # skip null moves
    if move:
        board.push_uci(move)

    # limit reached
    if depth > 5:
        return []

    results = engine.analyse(board, limit=chess.engine.Limit(depth=20), multipv=4)
    best_score = abs(results[0]["score"].relative.score(mate_score=100000))
    # Checkmate is on the board
    if results[0]["score"].relative.mate() == 0:
        return []

    # Only keep moves that are within eval_threshold
    # Mates are always kept

    # Some defensive programming because this broke sometimes
    if "pv" not in results[0]:
        return []

    best_move = results[0]["pv"][0].uci()
    score_cutoff = best_score - eval_threshold
    node_children = [(board.fen(), best_move)]

    for result in results[1:]:
        if abs(result["score"].relative.score(mate_score=100000)) > score_cutoff:
            move = result["pv"][0].uci()
            node_children.append((board.fen(), move))
        else:
            # Moves are in order of strength, so we can break prematurely
            break
    else:
        # break was not called, therefore we added ALL moves.
        # This means the position is completely lost for black
        # (all moves are equally bad - no further complications/tricks)
        # Make sure that we did actually add 4 moves and it's not too early
        if depth > 1 and len(node_children) == 4 and board.turn == chess.BLACK:
            return []
    
    # Play the best move if we are white (puzzle player)
    if board.turn == chess.WHITE:
        node_children = node_children[:1]
    return [(node, expand_tree(*node, engine=engine,
        eval_threshold=eval_threshold, depth=depth+1))
        for node in node_children]

def main():
    stockfish = chess.engine.SimpleEngine.popen_uci(sys.argv[1], timeout=None)
    df = pd.read_csv(sys.argv[2])

    puzzles = {}
    for _, row in df.iterrows():
        fen = row["white_to_play_FEN"]
        print(json.dumps([row["PuzzleId"], expand_tree(fen, chess.Move.null(), stockfish)]))
    stockfish.quit()

if __name__ == "__main__":
    main()
