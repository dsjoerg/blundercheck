
import chess.pgn
import chess
import pystockfish
import os, sys
import random
from djeval import *

# must be run from contest_* image, not from scoreserver, because it uses pandas

def mean(foo):
    return sum(foo) / len(foo)

def describe_movescores(ms):
# https://github.com/ornicar/lila/blob/master/modules/analyse/src/main/Advice.scala#L44-L47
    print "Avg cp loss:  ", mean(ms)
    print "Inaccuracies: ", sum((ms > -100) & (ms <= -50))
    print "Mistakes:     ", sum((ms > -300) & (ms <= -100))
    print "Blunders:     ", sum(              (ms <= -300))
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

for gamesread in range(0,int(sys.argv[1])):
    while random.random() > 0.01:
        game = chess.pgn.read_game(game_fd)

    msg("ANALYZING %s" % (game.headers['Event']))

    if backwards:
        result_struct = do_it_backwards(engine=engine, game=game, debug=DEBUG)
    else:
        result_struct = do_it(engine=engine, game=game, depth=depth, debug=DEBUG)

    describe_position_scores(result_struct['position_scores'])
    describe_position_scores(result_struct['massaged_position_scores'])

