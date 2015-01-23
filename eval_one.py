
import chess.pgn
import chess
import pystockfish
import os
from pandas import *


from djeval import *

def describe_position_scores(ps):
    ds = []
    ds.append(Series(ps).describe())
    ds.append((Series(ps).diff())[1::2].describe())
    ds.append((-1 * Series(ps).diff())[2::2].describe())
    print DataFrame(ds, index=['position scores', 'white gain', 'black gain'])


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

msg("Hi! Analyzing %s. Depth=%s, Movetime=%s" % (fname, str(depth), str(movetime)))

engine = pystockfish.Engine(depth=depth, param={'Threads':threads, 'Hash':hash}, movetime=movetime)

game_fd = open(fname, 'r')
game = chess.pgn.read_game(game_fd)

if backwards:
    result_struct = do_it_backwards(engine=engine, game=game, depth=depth, debug=DEBUG)
else:
    result_struct = do_it(engine=engine, game=game, depth=depth, debug=DEBUG)

describe_position_scores(result_struct['position_scores'])
describe_position_scores(result_struct['massaged_position_scores'])

