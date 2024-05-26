import chess
import zss
import chess.engine

class ChessTreeNode:
    def __init__(self, node, children, depth=0):
        fen, move = node
        board = chess.Board(fen)
        board.push(move)
        src, dst = move.from_square, move.to_square
        self.move_attributes = {
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
        board.pop()
        self.board = board
        self.mv = move

    def _print(self, n=0):
        print("    "*n + self.board.san(self.mv) + str(self.move_attributes))
        print()
        for c in self.children:
            c._print(n+1)

    @staticmethod
    def get_label(node):
        return node.move_attributes
    
    @staticmethod
    def get_children(node):
        return node.children
    
    @staticmethod
    def compare(a, b):
        # Adding/removing node
        # This depends on depth
        if a == "" or b == "":
            # Swap if needed
            if a == "":
                a, b = b, a
            depth_dict = {
                0: 2000,
                1: 1000,
                2: 250,
                3: 100,
                4: 50,
                5: 25
            }
            return depth_dict.get(a["depth"], 5000)
        # Compare 2 move attribute dictionaries.
        d = 0
        
        # Compare sides
        if a["side"] != b["side"]:
            d += 9999999999
        
        # Pieces
        if (p1 := a["piece"]) == (p2 := b["piece"]):
            pass
        elif {p1, p2} == {"R", "Q"}:
            d += 10
        elif {p1, p2} == {"B", "Q"}:
            d += 20
        else:
            d += 50
        
        # Squares
        if a["from_file"] != b["from_file"]:
            d += 5
        if a["from_rank"] != b["from_rank"]:
            d += 5
        if a["from_diagonal_1"] != b["from_diagonal_1"]:
            d += 5
        if a["from_diagonal_2"] != b["from_diagonal_2"]:
            d += 5

        if a["to_file"] != b["to_file"]:
            d += 5
        if a["to_rank"] != b["to_rank"]:
            d += 5
        if a["to_diagonal_1"] != b["to_diagonal_1"]:
            d += 5
        if a["to_diagonal_2"] != b["to_diagonal_2"]:
            d += 5

        d += abs(a["move_distance"] - b["move_distance"])

        if a["check"] != b["check"]:
            d += 10
 
        if a["mate"] != b["mate"]:
            d += 15
        
        d += 2 * abs(a["num_attacks"] - b["num_attacks"])
        d += 2 * abs(a["num_defenses"] - b["num_defenses"])
        d += 2 * abs(a["attacked_by_num"] - b["attacked_by_num"])
        d += 2 * abs(a["defended_by_num"] - b["defended_by_num"])

        return d

def expand_tree(fen, move, engine, can_terminate_on_equal_moves, eval_threshold=100, depth=0):
    print(fen, move)
    board = chess.Board(fen)
    # skip null moves
    if move:
        board.push(move)

    # limit reached
    if depth > 5:
        return []

    results = engine.analyse(board, limit=chess.engine.Limit(depth=15), multipv=3)
    best_score = results[0]["score"].relative.score(mate_score=100000)
    # Checkmate is on the board
    if results[0]["score"].relative.mate() == 0:
        return []

    # Only keep moves that are within eval_threshold
    # Mates are always kept
    best_move = results[0]["pv"][0]
    score_cutoff = best_score - eval_threshold
    node_children = [(board.fen(), best_move)]

    for result in results[1:]:
        diff = best_score - result["score"].relative.score(mate_score=100000)
        if result["score"].relative.score(mate_score=100000) > score_cutoff:
            move = result["pv"][0]
            node_children.append((board.fen(), move))
        else:
            # Moves are in order of strength, so we can break prematurely
            break
    else:
        # break was not called, therefore we added ALL moves.
        # This means the position could be completely winning (all moves are good)
        if can_terminate_on_equal_moves:
            return []

    return [(node, expand_tree(*node, engine, not can_terminate_on_equal_moves, 200 - eval_threshold, depth=depth+1))
        for node in node_children]

def main():
    magnus = "2R5/4bppk/1p1p4/5R1P/4PQ2/5P2/r4q1P/7K w - - 5 50"
    magnus2 = "5R2/bp4pk/2n3p1/P7/P1q3bP/6P1/3Q3K/1R6 w - - 1 32"
    motif1 = "4r1k1/1b3pp1/4p3/p2r4/7R/2B1Q1PP/P1P1RP1K/1q6 w - - 0 1"
    motif2 = "r5k1/5pp1/8/3p3R/2q4P/PbB2P2/1P1Q2P1/K7 w q - 0 1"

    stockfish = chess.engine.SimpleEngine.popen_uci("stockfish-ubuntu-x86-64-avx2/stockfish/stockfish-ubuntu-x86-64-avx2")
    tree1 = ChessTreeNode(*expand_tree(magnus, chess.Move.null(), stockfish, True)[0])
    tree2 = ChessTreeNode(*expand_tree(magnus2, chess.Move.null(), stockfish, True)[0])
    tree3 = ChessTreeNode(*expand_tree(motif1, chess.Move.null(), stockfish, True)[0])
    tree4 = ChessTreeNode(*expand_tree(motif2, chess.Move.null(), stockfish, True)[0])
    stockfish.quit()

    for i, x in enumerate([tree1, tree2, tree3, tree4]):
        for j, y in enumerate([tree1, tree2, tree3, tree4]):
            dist = zss.simple_distance(x, y, 
                ChessTreeNode.get_children,
                ChessTreeNode.get_label,
                ChessTreeNode.compare)
            print(f"{i},{j}: {dist}")
        print()



if __name__ == "__main__":
    main()
