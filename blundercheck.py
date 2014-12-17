
import chess.pgn
import chess
import urllib
import pystockfish
import sys
import os
import boto
import json
import StringIO
import time

class DSJURLopener(urllib.FancyURLopener):
    version = "dsjoerg"

urllib._urlopener = DSJURLopener()

DEBUG = ('BLUNDER_DEBUG' in os.environ)

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

    

def do_it(outfile, game=None, depth=15):

    outfile.write(game.headers['BCID'])
    outfile.write(' ')

    engine = pystockfish.Engine(depth=depth)
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

        if DEBUG:
            thismove_analysis = '%2d%-3s %6s loss:%5.0f (equity: %+5.0f) (best move: %s)' % (node.board().fullmove_number, turn_indicator, node.board().san(next_node.move), score_loss, next_score_white, node.board().san(best_move))
            print thismove_analysis
            #        print >>outfile, thismove_analysis

        outfile.write(score_loss)
        outfile.write(' ')
        outfile.write(next_score_white)
        outfile.write(' ')

        node = next_node
        current_score_white = next_score_white
        best_move = next_best_move

    outfile.write('\n')


config_bucket = os.environ['CONFIG_BUCKET']
config_key = os.environ['CONFIG_KEY']

conn = boto.connect_s3()
config_bucket = conn.get_bucket(config_bucket)
key = config_bucket.get_key(config_key)
runconfig = json.loads(key.get_contents_as_string())

pgn_key = runconfig['pgn_key']
depth = runconfig['depth']


print("%s Hi! Analyzing %s to depth %d" % (time.strftime('%Y%m%d-%H%M%S'), pgn_key,depth) )

inputs_bucket = conn.get_bucket('bc-runinputs')
games_key = inputs_bucket.get_key(pgn_key)
games_fd = StringIO.StringIO(games_key.get_contents_as_string())

analysis_string = StringIO.StringIO()

game = chess.pgn.read_game(games_fd)
while game is not None:
    do_it(analysis_string, game=game, depth=depth)
    game = chess.pgn.read_game(games_fd)

output_bucket = conn.get_bucket('bc-runoutputs')
new_key = runconfig['result_key']
key = output_bucket.new_key(new_key)
key.set_contents_from_string(analysis_string.getvalue())
analysis_string.close()

print("%s All done." % time.strftime('%Y%m%d-%H%M%S'))
