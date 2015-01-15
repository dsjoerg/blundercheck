import sys
import time
import urllib
import chess

# so that we can open URLs directly from lichess when needed
class DSJURLopener(urllib.FancyURLopener):
    version = "dsjoerg"

urllib._urlopener = DSJURLopener()

def msg(str):
    print "%s %s" % (time.strftime('%Y%m%d-%H%M%S'), str)
    sys.stdout.flush()

def score_node(engine, node):
    """
    Returns the score, in centipawns for white,
    for the position indicated by the given GameNode.
    
    If the position is won or illegal, return infinity.
    
    Also return the best move.
    """

    engine.setfen(node.board().fen())
    bestmove = engine.bestmove()
    score_cp = bestmove['score_cp']
    if score_cp is not None:
        score_cp_for_white = score_cp
    else:
        score_cp_for_white = float("inf")

    if node.board().turn == chess.BLACK:
        score_cp_for_white = -1 * score_cp_for_white

    if bestmove['move'] != '(none)':
        move_object = chess.Move.from_uci(bestmove['move'])
    else:
        move_object = None
        
    return (score_cp_for_white, move_object)


# returns a dict with:
# bcid: our 'blundercheck id' for the game
# position_scores: a list with one integer per ply, containing the score for that ply
# best_moves: a list with what the best move was at each ply
# runtime: how long in seconds it took to run do_it()

def do_it(engine, game=None, depth=15, debug=False):

    msg("Hi! Analyzing %s" % game.headers['Event'])

    begin_time = time.time()

    outstruct = {}
    outstruct['event'] = game.headers['Event']
    outstruct['position_scores'] = []
    outstruct['best_moves'] = []

    node = game

    (current_score_white, best_move) = score_node(engine, node)

    while node.variations:

        turn_indicator = '.'
        score_sign = 1
        if node.board().turn == chess.BLACK:
            turn_indicator = '...'
            score_sign = -1

        next_node = node.variation(0)
        (next_score_white, next_best_move) = score_node(engine, next_node)
        score_loss = score_sign * (current_score_white - next_score_white)

        # TODO only show (best move: foo) when the player didn't make that move
        # TODO count loss as zero when the player makes the best move?
        # TODO count loss as zero when player preserves mate count (rather than a loss of -1)

        if debug:
            thismove_analysis = '%2d%-3s %6s loss:%5.0f (equity: %+5.0f) (best move: %s)' % (node.board().fullmove_number, turn_indicator, node.board().san(next_node.move), score_loss, next_score_white, node.board().san(best_move))
            print thismove_analysis
            #        print >>outfile, thismove_analysis

        outstruct['position_scores'].append(next_score_white)
        outstruct['best_moves'].append(node.board().san(best_move))

        node = next_node
        current_score_white = next_score_white
        best_move = next_best_move

    outstruct['runtime'] = time.time() - begin_time
    return outstruct
