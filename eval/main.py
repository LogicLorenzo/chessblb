import chess, chess.engine, json, random, numpy


DEFENDER_DEPTH  = 5
ATTACKER_DEPTH  = 3
MASTER_DEPTH    = 10
NUMBER_MOVES    = 5
TREE_DEPTH      = 30
E_MIN           = 100  # centipawns
POINTS_LIM      = 5.5
SPREAD_CP       = 100
TOP_COUNT       = 10
PATH            = "/opt/homebrew/bin/stockfish"
START_FEN       = "r1bqk2r/ppp2ppp/2np1n2/2b1p3/2B1P3/2NP1N2/PPP2PPP/R1BQK2R w KQkq - 4 6"
OUT_FILE        = "hidden_positions.jsonl"
GAME_ID         = "italian_game"

def analyse_pos(board, engine, depth):
    info = engine.analyse(board, chess.engine.Limit(depth=depth))
    # score() might be None in mate-ladder scenarios; skip those if you like
    return info["score"].pov(board.turn).score()

def has_free_capture(board):
    """
    Return True if there exists a capture move such that,
    after capturing, the capturing piece is NOT attacked
    by any of the opponent's pieces.
    """
    for move in board.generate_legal_moves():
        if board.is_capture(move):
            board.push(move)
            to_sq   = move.to_square
            attacker = board.turn            # after push, .turn is the defender
            attacked = board.is_attacked_by(attacker, to_sq)
            board.pop()
            if not attacked:
                return True
    return False
    
def material_count(board):
    points = [  len(board.pieces(chess.PAWN, chess.BLACK)) \
                + 3 * len(board.pieces(chess.BISHOP, chess.BLACK))  \
                + 3 * len(board.pieces(chess.KNIGHT, chess.BLACK))  \
                + 5 * len(board.pieces(chess.ROOK, chess.BLACK))    \
                + 9 * len(board.pieces(chess.QUEEN, chess.BLACK))   , 
                len(board.pieces(chess.PAWN, chess.WHITE)) \
                + 3 * len(board.pieces(chess.BISHOP, chess.WHITE))  \
                + 3 * len(board.pieces(chess.KNIGHT, chess.WHITE))  \
                + 5 * len(board.pieces(chess.ROOK, chess.WHITE))    \
                + 9 * len(board.pieces(chess.QUEEN, chess.WHITE))
            ]
    return points[1] - points[0]
    
def is_queen_attacked(board, color):
    queens = board.pieces(chess.QUEEN, color)
    if not queens:
        return False
    for sq in queens:
        if board.is_attacked_by(not color, sq):
            return True
    return False

def explore_tree(fen, depth_left, output_file, game_id):
    import chess.engine
    defender = chess.engine.SimpleEngine.popen_uci(PATH)
    attacker = chess.engine.SimpleEngine.popen_uci(PATH)
    master   = chess.engine.SimpleEngine.popen_uci(PATH)
    board = chess.Board(fen)

    def close_engines():
        defender.quit()
        attacker.quit()
        master.quit()

    def visit_node(board, results):
        shallow_engine = defender if board.turn else attacker
        eval_shallow = analyse_pos(board, shallow_engine, DEFENDER_DEPTH if board.turn else ATTACKER_DEPTH)
        eval_deep    = analyse_pos(board, master, MASTER_DEPTH)

        # check if mate is forced
        if eval_shallow is None or eval_deep is None:
            return

        # check if the evaluation for deeper engine is larger than limit
        eval_diff = abs(eval_deep - eval_shallow)
        if eval_diff < E_MIN:
            return
        
        # check if there are free attacks
        if has_free_capture(board):
            return
        
        # check if queens are under attack
        if board.turn:  # white to move → black queen must be vulnerable
            if not is_queen_attacked(board, chess.BLACK):
                return
        else:           # black to move → white queen must be vulnerable
            if not is_queen_attacked(board, chess.WHITE):
                return

        # check if there is a material imbalance
        if abs(material_count(board)) > POINTS_LIM:
            return
        
        # check if one side is too strong
        if abs(eval_deep) > 1000:
            return

        try:
            lines = master.analyse(
                board,
                chess.engine.Limit(depth=MASTER_DEPTH),
                multipv=TOP_COUNT
            )
        except Exception:
            return

        evals = [pv["score"].pov(board.turn).score() for pv in lines if pv["score"].pov(board.turn).score() is not None]
        if len(evals) < 2:
            return
        spread = abs(evals[0] - evals[-1])
        if spread < SPREAD_CP:
            return

        record = {
            "ID": game_id,
            "ply": board.ply(),
            "fen": board.fen(),
            "eval_shallow": eval_shallow,
            "eval_deep": eval_deep,
            "spread": spread,
            "evals": evals
        }
        results.write(json.dumps(record) + "\n")

    def recurse(board, depth_left):
        if depth_left == 0 or board.is_game_over():
            return

        visit_node(board, results)

        try:
            lines = master.analyse(
                board,
                chess.engine.Limit(depth=MASTER_DEPTH),
                multipv=NUMBER_MOVES
            )
        except Exception:
            return

        for line in lines:
            move = line["pv"][0]
            board.push(move)
            recurse(board, depth_left - 1)
            board.pop()

    with open(output_file, "a+") as results:
        try:
            recurse(board, depth_left)
        finally:
            close_engines()

explore_tree(START_FEN, TREE_DEPTH, OUT_FILE, GAME_ID)