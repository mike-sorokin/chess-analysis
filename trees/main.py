import chess
import chess.engine

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


def print_tree(t, ind=0):
    for (b, m), st in t:
        print("    "*ind + chess.Board(b).san(m))
        print_tree(st, ind+1)

def main():
    simple_br = "4r1k1/1b3pp1/4p3/p2r4/7R/2B1Q1PP/P1P1RP1K/1q6 w - - 0 1"
    magnus = "2R5/4bppk/1p1p4/5R1P/4PQ2/5P2/r4q1P/7K w - - 5 50"
    simple = "2k2br1/pp1r4/2n5/4p1B1/P1NpP1qp/3P1R2/1P2Q2P/7K w - - 0 1"

    stockfish = chess.engine.SimpleEngine.popen_uci("stockfish-ubuntu-x86-64-avx2/stockfish/stockfish-ubuntu-x86-64-avx2")
    tree = expand_tree(simple, chess.Move.null(), stockfish, True)
    stockfish.quit()
    print_tree(tree)

if __name__ == "__main__":
    main()
