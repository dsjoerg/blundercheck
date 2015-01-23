
import chess.pgn
import chess
import pystockfish
import os
import numpy
import random
from pandas import *


from djeval import *

def describe_movescores(ms):
# https://github.com/ornicar/lila/blob/master/modules/analyse/src/main/Advice.scala#L44-L47
    print "Avg cp loss:  ", numpy.mean(ms)
    print "Inaccuracies: ", numpy.sum((ms > -100) & (ms <= -50))
    print "Mistakes:     ", numpy.sum((ms > -300) & (ms <= -100))
    print "Blunders:     ", numpy.sum(              (ms <= -300))
    print ms.describe()

def describe_position_scores(ps):
    ds = []
    print "POSITION SCORES"
    sps = Series(ps)
    print sps.describe()

    clipped_sps = sps.clip(-999,999)

    print "WHITE"
    describe_movescores((clipped_sps.diff())[1::2])

    print "BLACK"
    describe_movescores((-1 * clipped_sps.diff())[2::2])


DEBUG = ('DEBUG' in os.environ)

if 'THREADS' in os.environ:
    threads = int(os.environ['THREADS'])
else:
    threads = 1

if 'HASH' in os.environ:
    hash = int(os.environ['HASH'])
else:
    hash = 100

backwards = ('BACKWARDS' in os.environ)
fname = os.environ['FNAME']

depth = None
if 'DEPTH' in os.environ:
    depth = int(os.environ['DEPTH'])

movetime = None
if 'MOVETIME' in os.environ:
    movetime = int(os.environ['MOVETIME'])
    depth = None

engine = pystockfish.Engine(depth=depth, param={'Threads':threads, 'Hash':hash}, movetime=movetime)

game_fd = open(fname, 'r')

for gamesread in range(0,10):
    while random.random() > 0.01:
        game = chess.pgn.read_game(game_fd)

    msg("ANALYZING %s" % (game.headers['Event']))

    if backwards:
        result_struct = do_it_backwards(engine=engine, game=game, depth=depth, debug=DEBUG)
    else:
        result_struct = do_it(engine=engine, game=game, depth=depth, debug=DEBUG)

    describe_position_scores(result_struct['position_scores'])
    describe_position_scores(result_struct['massaged_position_scores'])

