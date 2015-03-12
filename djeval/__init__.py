import sys, time, urllib, code
from chess import *

NUM_GB_DEPTHS = 18

INFO_DEPTH = 0
INFO_SELDEPTH = 1
INFO_SCORE = 2
INFO_NODES = 3
INFO_BESTMOVE = 4
INFO_PVNUM = 5
INFO_COMPTIME = 6

ANALYSIS_TIME_USEBEST = 999999

def shell():
    vars = globals()
    vars.update(locals())
    shell = code.InteractiveConsole(vars)
    shell.interact()

# so that we can open URLs directly from lichess when needed
class DSJURLopener(urllib.FancyURLopener):
    version = "dsjoerg"

urllib._urlopener = DSJURLopener()

def msg(str):
    sys.stderr.write("%s %s\n" % (time.strftime('%Y%m%d-%H%M%S'), str))
    sys.stderr.flush()

def hash32(game):
    node = game
    halfply = 0
    while node.variations:
        halfply = halfply + 1
        if halfply == 32:
            return node.board().zobrist_hash()
        node = node.variation(0)
    return 0

# returns "NE", "SW" etc for a move, from the players perspective
# and also the distance moved
def move_direction_and_distance(board, move):

    from_file = file_index(move.from_square)
    from_rank = rank_index(move.from_square)
    to_file = file_index(move.to_square)
    to_rank = rank_index(move.to_square)
    file_move = to_file - from_file
    rank_move = to_rank - from_rank
    if board.turn == BLACK:
        file_move = -1 * file_move
        rank_move = -1 * rank_move

    ns_letter = ""
    if rank_move > 0:
        ns_letter = "N"
    elif rank_move < 0:
        ns_letter = "S"
    
    ew_letter = ""
    if file_move > 0:
        ew_letter = "E"
    elif file_move < 0:
        ew_letter = "W"


    return (ns_letter + ew_letter), max(abs(file_move), abs(rank_move))


# returns a list representing the features of this move
def features(board, move):
    if move is None:
        return ["", "", 0, False, False]

    move_dir, move_dist = move_direction_and_distance(board, move)
    board.push(move)
    is_check = board.is_check()
    board.pop()
    result = [board.piece_at(move.from_square).symbol().upper(),
              move_dir,
              move_dist,
              board.piece_at(move.to_square) is not None,
              is_check]
    return result


def fix_score(score):
    if score is None:
        return 32768
    return score


def score_node(engine, node):
    """
    Returns the score, in centipawns for white,
    for the position indicated by the given GameNode.
    
    If the position is won or illegal, return infinity.
    
    Also return the best move.
    """

    engine.setfen(node.board().fen())
    bestmove = engine.bestmove()
    score_cp_for_white = fix_score(bestmove['score_cp'])

    if node.board().turn == BLACK:
        score_cp_for_white = -1 * score_cp_for_white

    if bestmove['move'] != '(none)':
        move_object = Move.from_uci(bestmove['move'])
    else:
        move_object = None
        
    return (score_cp_for_white, move_object)


def guid_bratko_score(infos):
    """
Guid, M. and Bratko, I. Computer Analysis of World Chess Champions. ICGA
Journal, Vol. 29, No. 2, pp. 65-73, 2006. [GB06]

    difficulty := 0;
    for depth 2 to 12 do
      if (depth > 2) and (previous best move not equals current best move) then
        difficulty += |best move evaluation - second best move evaluation|
      end if
    end for
    """
    difficulty = 0
    difficulty_12 = 0
    difficulties = [0]*(NUM_GB_DEPTHS+1)
    
    max_depth = infos[-1][INFO_DEPTH]

    # make a dictionary mapping from (depth, multipv) to info
    infodict = dict([[(info[INFO_DEPTH], info[INFO_PVNUM]), info] for info in infos])

    prev_bestmove = infodict[(2, 1)][INFO_BESTMOVE]
    for depth in range(3, max_depth + 1):
        if ((depth, 1) in infodict) and ((depth, 2) in infodict):
            bestmove = infodict[(depth, 1)][INFO_BESTMOVE]
            if (prev_bestmove != bestmove):
                best_score = fix_score(infodict[(depth, 1)][INFO_SCORE])
                secondbest_score = fix_score(infodict[(depth, 2)][INFO_SCORE])
                bestmove_advantage = abs(best_score - secondbest_score)
                if bestmove_advantage > 200:
                    bestmove_advantage = 200
                difficulty += bestmove_advantage
                if depth < NUM_GB_DEPTHS:
                    difficulties[depth] += bestmove_advantage
                else:
                    difficulties[NUM_GB_DEPTHS] += bestmove_advantage
#                print "At depth %i, difficulty increased to %i" % (depth, difficulty)
                if depth <= 12:
                    difficulty_12 += bestmove_advantage
                prev_bestmove = bestmove

    return difficulty, difficulty_12, difficulties


def process_sf_infos(infos, node, material_info, best_move_uci):
    """
    Returns [depth, seldepth, score, nodes, best_move,
    depths_agreeing, deepest_agree, white_material, black_material,
    game_phase, gb_complexity, gb_complexity_12, gbN]
    """

    actual_move_uci = node.variation(0).move.uci() if node.variations else ""

    # get the infos for the best line
    pv1_infos = [info for info in infos if info[INFO_PVNUM] == 1]

    if len(pv1_infos) == 0:
        print "No infos!"
        depth = 0
        seldepth = 0
        nodes = 0
        if node.board().turn == WHITE:
            print "white mated, white has no move to make, white has neg Inf score"
            score_cp_for_white = -32768
        else:
            print "blacks mated, no move to make, white has Inf score"
            score_cp_for_white = 32768
        deepest_agree = 0
        depths_agreeing = 0
        num_bestmoves = 0
        num_bestmove_changes = 0
        bestmove_depths_agreeing = 0
        deepest_change = 0
        gb_complexity = 0
        gb_complexity_12 = 0
        gb_complexities = [0] * (NUM_GB_DEPTHS+1)
        best_move_object = None
    else:
        if best_move_uci is None:
            # rather than take the best move from the last line that stockfish prints, we
            # take the last completed depth with a timestamp.
            #
            # that means we are throwing away some computation each time, but it's the only
            # way to get a consistent measure of the power of increasing depth/time
            #
            best_move_uci = pv1_infos[-1][INFO_BESTMOVE]

        if best_move_uci != '(none)':
            best_move_object = Move.from_uci(best_move_uci)
        else:
            best_move_object = None


        depth = pv1_infos[-1][INFO_DEPTH]
        seldepth = pv1_infos[-1][INFO_SELDEPTH]
        nodes = pv1_infos[-1][INFO_NODES]

        score_cp_for_white = fix_score(pv1_infos[-1][INFO_SCORE])

        if node.board().turn == BLACK:
            score_cp_for_white = -1 * score_cp_for_white

#        print "infos=%s" % str(infos)
#        print "amu=%s. bestmoves at various depths %s" % (actual_move_uci, str([i[4] for i in infos]))

        agreeing_depths = [i[0] for i in pv1_infos if i[INFO_BESTMOVE] == actual_move_uci]
        depths_agreeing = len(agreeing_depths)
        deepest_agree = agreeing_depths[-1] if depths_agreeing > 0 else 0
        
        bestmoves = [i[INFO_BESTMOVE] for i in pv1_infos]
        bestmoves.append(best_move_uci)
        num_bestmoves = len(set(bestmoves))

        bestmove_changes = [i for i in range(0,len(bestmoves)-1) if bestmoves[i] != bestmoves[i+1]]
        num_bestmove_changes = len(bestmove_changes)
        if num_bestmove_changes > 0:
            deepest_change = bestmove_changes[-1] + 1
        else:
            deepest_change = 0

        bestmove_agreeing_depths = [i[INFO_DEPTH] for i in pv1_infos if i[INFO_BESTMOVE] == best_move_uci]
        bestmove_depths_agreeing = len(bestmove_agreeing_depths)
        gb_complexity, gb_complexity_12, gb_complexities = guid_bratko_score(infos)

    retval = [depth, seldepth, score_cp_for_white, nodes, best_move_object, depths_agreeing, deepest_agree, num_bestmoves, num_bestmove_changes, bestmove_depths_agreeing, deepest_change]
    retval.extend(material_info)
    retval.extend([gb_complexity, gb_complexity_12, gb_complexities])

    return retval

    

def score_node_and_move(engine, node, analysis_times):
    """

    Returns [[depth, seldepth, score, nodes, best_move,
    depths_agreeing, deepest_agree, white_material, black_material,
    game_phase, gb_complexity, gb_complexity_12, gbN], ...]

    One for each of the analysis_times.

    
    depth = deepest depth that the engine was able to search all branches.
            due to hashing from previous searches it may not be strictly
            a function of the position.

    seldepth = a debatably useful measure of selective further depth

    score = the score, in centipawns for white, for the position indicated
            by the given GameNode.
    
            If the position is won, return 32768 for white or -32768 for black.
    
    nodes = the number of nodes the engine was able to evaluate.  Expect this
            to be quite stable since we are running for a fixed amount of time
 
    best_move = the engine's best move

    depths_agreeing = the number of depths that agree with the move actually made

    deepest_agree = the deepest depth that agrees with the move made

    num_bestmoves = how many different bestmoves were there during the evaluation
    
    num_bestmove_changes = the number of times the bestmove changed

    bestmove_depths = the number of depths that agree with the bestmove

    deepest_change = the # of the deepest depth at which the bestmove changed

    white_material = standard-scored material value of current position, for white
    black_material = standard-scored material value of current position, for black
    game_phase = game phase using Stockfish criteria. midgame=128, endgame=0
    
    gb_complexity = guid-bratko complexity score for each move, using all depths
    gb_complexity_12 = guid-bratko complexity score for each move, using no more than 12 depths
    gbN = guid-bratko complexity score per depth, averaged across all moves

    """

    material_info = engine.setfen(node.board().fen())

    result = engine.go_infos()

    infos = result['infos']

    retval = []
    for analysis_time in analysis_times:
        infos_for_analysis = [info for info in infos if info[INFO_COMPTIME] < analysis_time]

        if analysis_time == ANALYSIS_TIME_USEBEST:
            best_move_uci = result['move']
        else:
            best_move_uci = None

#        print "There are %i infos for analysis at analysis_time %i" % (len(infos_for_analysis), analysis_time)
#        print "They are: %s" % infos_for_analysis
        retval.append(process_sf_infos(infos_for_analysis, node, material_info, best_move_uci))

    return retval


# Given a list of position scores, 
def massage_position_scores(position_scores, was_bestmove):

#    print "YOOOOO", position_scores, was_bestmove
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
        if node.board().turn == BLACK:
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


def do_it_backwards(engine, game=None, debug=False, movenum=None):

    msg("Yo ho ho! Analyzing %s BACKWARDS" % game.headers['Event'])

    if movenum:
        movetime = engine.movetime
        engine.movetime = 1

    analysis_times = [2000, 4000, 8000, ANALYSIS_TIME_USEBEST]

    begin_time = time.time()

    outstruct = {}
    outstruct['event'] = game.headers['Event']
    outstruct['position_scores'] = [list() for _ in xrange(len(analysis_times))]
    outstruct['best_moves'] = [list() for _ in xrange(len(analysis_times))]
    outstruct['move_features'] = [list() for _ in xrange(len(analysis_times))]
    outstruct['best_move_features'] = [list() for _ in xrange(len(analysis_times))]
    outstruct['depth_stats'] = [list() for _ in xrange(len(analysis_times))]
    outstruct['material_stats'] = [list() for _ in xrange(len(analysis_times))]
    outstruct['gb'] = [list() for _ in xrange(len(analysis_times))]
    outstruct['gb12'] = [list() for _ in xrange(len(analysis_times))]
    outstruct['gbN'] = [list([0] * (NUM_GB_DEPTHS+1)) for _ in xrange(len(analysis_times))]

    was_bestmove = [list() for _ in xrange(len(analysis_times))]

    node = game.end()


    scoreresults = score_node_and_move(engine, node, analysis_times)
    current_score_white = [scoreresult[2] for scoreresult in scoreresults]
    best_move = [scoreresult[4] for scoreresult in scoreresults]

    while node.parent:

        turn_indicator = '.'
        score_sign = 1
        if node.board().turn == WHITE:
            turn_indicator = '...'
            score_sign = -1

        prev_node = node.parent

        if movenum:
            if prev_node and (prev_node.board().fullmove_number != movenum) and (prev_node.board().fullmove_number != (movenum - 1)):
                engine.movetime = 1
                engine.debug = False
            else:
                engine.movetime = movetime
                engine.debug = True

        # clear the hash before each move eval so that depth stats are clean
        engine.put('setoption name Clear Hash')
#        engine.debug = True
#        engine.put('setoption name multipv value 2')

        scoreresults = score_node_and_move(engine, prev_node, analysis_times)
        prev_score_white = [scoreresult[2] for scoreresult in scoreresults]
        prev_best_move = [scoreresult[4] for scoreresult in scoreresults]

        if debug:
            for i in range(0, len(prev_score_white)):
                score_loss = score_sign * (prev_score_white[i] - current_score_white[i])
                thismove_analysis = '%s: %2d%-3s %6s loss:%5.0f (%+5.0f -> %+5.0f) (best move: %s) (depth %i, seldepth %i) (%i depths agree, deepest %i)' % (game.headers['Event'], prev_node.board().fullmove_number, turn_indicator, prev_node.board().san(node.move), score_loss, prev_score_white[i], current_score_white[i], prev_node.board().san(prev_best_move[i]), scoreresults[i][0], scoreresults[i][1], scoreresults[i][5], scoreresults[i][6])
                print thismove_analysis
                sys.stdout.flush()
            #        print >>outfile, thismove_analysis
        else:
            print '.',

        for i in range(0, len(prev_score_white)):
            outstruct['position_scores'][i].insert(0, current_score_white[i])
#            print "i=%i, csw[i]=%s, o['p_s'][i]=%s" % (i, current_score_white[i], outstruct['position_scores'][i])
            outstruct['best_moves'][i].insert(0, prev_node.board().san(prev_best_move[i]))
            outstruct['move_features'][i].insert(0, features(prev_node.board(), node.move))
            outstruct['best_move_features'][i].insert(0, features(prev_node.board(), prev_best_move[i]))

            depth_stats = [scoreresults[i][0], scoreresults[i][1]]
            depth_stats.extend(scoreresults[i][5:11])
            outstruct['depth_stats'][i].insert(0, depth_stats)
            outstruct['material_stats'][i].insert(0, scoreresults[i][11:14])
            outstruct['gb'][i].insert(0, scoreresults[i][14])
            outstruct['gb12'][i].insert(0, scoreresults[i][15])
            for j in range(0,NUM_GB_DEPTHS+1):
                outstruct['gbN'][i][j] += scoreresults[i][16][j]

            was_bestmove[i].insert(0, prev_best_move[i] == node.move)

        node = prev_node
        current_score_white = prev_score_white
        best_move = prev_best_move


    outstruct['massaged_position_scores'] = []
    for i in range(0, len(prev_score_white)):
        outstruct['position_scores'][i].insert(0, current_score_white[i])
        outstruct['massaged_position_scores'].append(massage_position_scores(outstruct['position_scores'][i], was_bestmove[i]))
        mps = outstruct['massaged_position_scores'][i]

        node = game

    #    print "YO", len(mps)
        if debug:
            score_index = 0
            while node.variations:

                turn_indicator = '.'
                score_sign = 1
                if node.board().turn == BLACK:
                    turn_indicator = '...'
                    score_sign = score_sign * -1

                next_node = node.variation(0)
                score_loss = score_sign * (mps[score_index] - mps[score_index + 1])

                thismove_analysis = '%s: %2d%-3s %6s loss:%5.0f (%+5.0f -> %+5.0f) (best move: %s) (depth %i, seldepth %i) (%i depths agree, deepest %i)' % (game.headers['Event'], node.board().fullmove_number, turn_indicator, node.board().san(next_node.move), score_loss, mps[score_index], mps[score_index+1], outstruct['best_moves'][i][score_index], outstruct['depth_stats'][i][score_index][0], outstruct['depth_stats'][i][score_index][1], outstruct['depth_stats'][i][score_index][2], outstruct['depth_stats'][i][score_index][3])
                print thismove_analysis
                sys.stdout.flush()

                node = next_node
                score_index = score_index + 1


#    print outstruct['position_scores']
    outstruct['runtime'] = time.time() - begin_time
    outstruct['movetime'] = engine.movetime
    print '\n'
    return outstruct

