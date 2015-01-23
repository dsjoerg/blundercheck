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
        score_cp_for_white = 32768

    if node.board().turn == chess.BLACK:
        score_cp_for_white = -1 * score_cp_for_white

    if bestmove['move'] != '(none)':
        move_object = chess.Move.from_uci(bestmove['move'])
    else:
        move_object = None
        
    return (score_cp_for_white, move_object)


# Given a list of position scores, 
def massage_position_scores(position_scores, was_bestmove):

#    print "YOOOOO", position_scores
    massaged_scores = list(position_scores)

    bestmoves_plus = list(was_bestmove)
    bestmoves_plus.append(False)

    side = -1
    for ix, score in enumerate(position_scores):
        if ix > 0:
            white_score_gain = score - massaged_scores[ix-1]
            player_score_gain = side * white_score_gain
            if bestmoves_plus[ix-1] or player_score_gain > 0:
                massaged_scores[ix] = massaged_scores[ix-1]
#            print ix, side, score, massaged_scores[ix-1], player_score_gain, bestmoves_plus[ix-1], massaged_scores[ix]
#            print "%i: side %i score %i prev %i gain %i bestmove %s massaged %i" % (ix, side, score, massaged_scores[ix-1], player_score_gain, bestmoves_plus[ix-1], massaged_scores[ix])
        side = side * -1


    return massaged_scores


# returns a dict with:
# bcid: our 'blundercheck id' for the game
# position_scores: a list with one integer per ply, containing the score for that ply
# best_moves: a list with what the best move was at each ply
# runtime: how long in seconds it took to run do_it()

def do_it(engine, game=None, debug=False):

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
            thismove_analysis = '%2d%-3s %6s loss:%5.0f (%+5.0f -> %+5.0f) (best move: %s)' % (node.board().fullmove_number, turn_indicator, node.board().san(next_node.move), score_loss, current_score_white, next_score_white, node.board().san(best_move))
            print thismove_analysis
            #        print >>outfile, thismove_analysis
        else:
            print '.',

        outstruct['position_scores'].append(next_score_white)
        outstruct['best_moves'].append(node.board().san(best_move))

        node = next_node
        current_score_white = next_score_white
        best_move = next_best_move

    outstruct['runtime'] = time.time() - begin_time
    print '\n'
    return outstruct


def do_it_backwards(engine, game=None, debug=False):

    msg("Hi! Analyzing %s BACKWARDS" % game.headers['Event'])

    begin_time = time.time()

    outstruct = {}
    outstruct['event'] = game.headers['Event']
    outstruct['position_scores'] = []
    outstruct['best_moves'] = []

    was_bestmove = []

    node = game.end()

    (current_score_white, best_move) = score_node(engine, node)

    while node.parent:

        turn_indicator = '.'
        score_sign = 1
        if node.board().turn == chess.WHITE:
            turn_indicator = '...'
            score_sign = -1

        prev_node = node.parent
        (prev_score_white, prev_best_move) = score_node(engine, prev_node)
        score_loss = score_sign * (prev_score_white - current_score_white)

        if debug:
            thismove_analysis = '%2d%-3s %6s loss:%5.0f (%+5.0f -> %+5.0f) (best move: %s)' % (prev_node.board().fullmove_number, turn_indicator, prev_node.board().san(node.move), score_loss, prev_score_white, current_score_white, prev_node.board().san(prev_best_move))
            print thismove_analysis
            #        print >>outfile, thismove_analysis
        else:
            print '.',

        outstruct['position_scores'].insert(0, current_score_white)
        outstruct['best_moves'].insert(0, prev_node.board().san(prev_best_move))
        was_bestmove.insert(0, prev_best_move == node.move)

        node = prev_node
        current_score_white = prev_score_white
        best_move = prev_best_move


    outstruct['position_scores'].insert(0, current_score_white)
    outstruct['massaged_position_scores'] = massage_position_scores(outstruct['position_scores'], was_bestmove)
    mps = outstruct['massaged_position_scores']

    node = game

#    print "YO", len(mps)
    if debug:
        score_index = 0
        while node.variations:

            turn_indicator = '.'
            score_sign = 1
            if node.board().turn == chess.BLACK:
                turn_indicator = '...'
                score_sign = score_sign * -1

            next_node = node.variation(0)
            score_loss = score_sign * (mps[score_index] - mps[score_index + 1])

            thismove_analysis = '%2d%-3s %6s loss:%5.0f (%+5.0f -> %+5.0f) (best move: %s)' % (node.board().fullmove_number, turn_indicator, node.board().san(next_node.move), score_loss, mps[score_index], mps[score_index+1], outstruct['best_moves'][score_index])
            print thismove_analysis

            node = next_node
            score_index = score_index + 1


#    print outstruct['position_scores']
    outstruct['runtime'] = time.time() - begin_time
    outstruct['movetime'] = time.time() - begin_time
    print '\n'
    return outstruct
