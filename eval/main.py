import chess, chess.engine, chess.svg, json

## Parameters
# Engine parameters
DEFENDER_DEPTH  = 5     # The depth for the defender (side with a disadvantage)
ATTACKER_DEPTH  = 3     # The depth for the attacker (side with an advantage)
MASTER_DEPTH    = 10    # The depth for the master engine (to evaluate)

# Evaluation parameters
NUMBER_MOVES    = 3     # Number of moves to explore at each node
TREE_DEPTH      = 3     # Maximum depth of the search tree
TOP_COUNT       = 5     # Number of lines for engine to evaluate for spread

# Interesting game criteria
E_MIN           = 100   # The minimum difference in centipawns for position to be interesting
POINTS_LIM      = 5.5   # Maximum amount of material imbalance 
SPREAD_CP       = 100   # The spread between top and bottom move

# Paths and files
STK_PATH        = "/opt/homebrew/bin/stockfish"
OUT_FILE        = "hidden_positions.jsonl"

# Game parameters
START_FEN       = "r1bqk2r/ppp2ppp/2np1n2/2b1p3/2B1P3/2NP1N2/PPP2PPP/R1BQK2R w KQkq - 4 6"
GAME_ID         = "ITAL"        # Italian Game

def analyse_pos(board, engine, depth):  # Analyse the current position
    info = engine.analyse(board, chess.engine.Limit(depth=depth))
    # score() might be None in mate-ladder scenarios; skip those if you like
    return info["score"].pov(board.turn).score()

def has_free_capture(board):  # Check if there is a free capture available on board
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
            if not attacked:  #TODO: add a condition for checking gambits (eval of master engine < gambit_coef * value of piece)
                return True
    return False
    
def material_count(board):  # (WORKS) Count material balance
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
    
def is_queen_attacked(board, color):  # (WORKS) Check if queens are free for capture
    queens = board.pieces(chess.QUEEN, color)
    if not queens:
        return False
    for sq in queens:
        if board.is_attacked_by(not color, sq):
            return True
    return False

def visit_node(defender, attacker, master, board, results):  # Explore the correct position
    shallow_engine = defender if board.turn else attacker
    eval_shallow = analyse_pos(board, shallow_engine, DEFENDER_DEPTH if board.turn else ATTACKER_DEPTH)
    eval_deep    = analyse_pos(board, master, MASTER_DEPTH)

    # Conditions for interesting game
    # check if mate is forced
    if eval_shallow is None or eval_deep is None: return

    # check if the evaluation for deeper engine is larger than limit
    eval_diff = abs(eval_deep - eval_shallow)
    if eval_diff < E_MIN: return
    
    # check if there are free attacks
    if has_free_capture(board): return
    
    # check if queens are under attack
    if board.turn:  # white to move → black queen must be vulnerable
        if not is_queen_attacked(board, chess.BLACK): return
    else:           # black to move → white queen must be vulnerable
        if not is_queen_attacked(board, chess.WHITE): return

    # check if there is a material imbalance
    if abs(material_count(board)) > POINTS_LIM:
        return
    
    # check if one side is too strong
    if abs(eval_deep) > 1000: return

    try: lines = master.analyse(board, chess.engine.Limit(depth=MASTER_DEPTH), multipv=TOP_COUNT)
    except Exception:
        return

    evals = [pv["score"].pov(board.turn).score() for pv in lines if pv["score"].pov(board.turn).score() is not None]
    
    # Second set of conditions for interesting games
    # Check if there are few moves
    if len(evals) < 2:
        return
    
    spread = abs(evals[0] - evals[-1])
    if spread < SPREAD_CP:
        return

    # Record second position
    record = {
        "ply": board.ply(),
        "fen": board.fen(),
        "eval_shallow": eval_shallow,
        "eval_deep": eval_deep,
        "spread": spread,
        "evals": evals
    }
    results.write(json.dumps(record) + "\n")

def explore_tree(fen, depth_left, output_file):  # Explore the game tree recursively from an initial position
    defender = chess.engine.SimpleEngine.popen_uci(STK_PATH)
    attacker = chess.engine.SimpleEngine.popen_uci(STK_PATH)
    master   = chess.engine.SimpleEngine.popen_uci(STK_PATH)
    board = chess.Board(fen)

    def recurse(board, depth_left):  # Recursively explore the game tree
        
        if depth_left == 0 or board.is_game_over(): return # End recursion if at depth limit or the game has ended

        visit_node(defender, attacker, master, board, results)

        try: lines = master.analyse(board, chess.engine.Limit(depth=MASTER_DEPTH), multipv=NUMBER_MOVES) # Analyse the position
        except Exception as e: raise Exception(f"{e}: Engine failed to analyse position")

        for line in lines: # Explore top moves in the position
            move = line["pv"][0]
            board.push(move)
            recurse(board, depth_left - 1)
            board.pop()

    with open(output_file, "a+") as results:  # Write to output file 
        try:
            recurse(board, depth_left)
        finally:
            defender.quit()
            attacker.quit()
            master.quit()

if "__main__" == __name__: 
    board = chess.Board(fen=START_FEN)
    with open("board.svg", "w") as f: f.write(chess.svg.board(board, size=400))
if "__main__" != __name__: explore_tree(START_FEN, TREE_DEPTH, OUT_FILE)  # Run the program, explore tree