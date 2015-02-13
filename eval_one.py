
import chess.pgn
import chess
import pystockfish
import os, StringIO
import numpy
from pandas import *
import boto
from boto.s3.key import Key

from djeval import *

def get_game_from_s3(game_number):
    s3conn = boto.connect_s3()
    gamesbucket = s3conn.get_bucket('bc-games')
    key_name = "kaggle/%s.pgn" % game_number
    msg("Retrieving %s" % key_name)
    k = gamesbucket.get_key(key_name)
    game_pgn_string = k.get_contents_as_string()
    msg("Game is %s" % game_pgn_string)
    game_fd = StringIO.StringIO(game_pgn_string)
    game = chess.pgn.read_game(game_fd)


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
game_number = int(os.environ['GAMENUM'])

depth = None
if 'DEPTH' in os.environ:
    depth = int(os.environ['DEPTH'])

movetime = None
if 'MOVETIME' in os.environ:
    movetime = int(os.environ['MOVETIME'])
    depth = None

movenum=None
if 'MOVENUM' in os.environ:
    movenum = int(os.environ['MOVENUM'])

msg("Hi! Analyzing %i. Depth=%s, Movetime=%s" % (game_number, str(depth), str(movetime)))

engine = pystockfish.Engine(depth=depth, param={'Threads':threads, 'Hash':hash}, movetime=movetime)

game = get_game_from_s3(game_number)

if backwards:
    result_struct = do_it_backwards(engine=engine, game=game, debug=DEBUG, movenum=movenum)
else:
    result_struct = do_it(engine=engine, game=game, depth=depth, debug=DEBUG)

print result_struct
#describe_position_scores(result_struct['position_scores'])
#describe_position_scores(result_struct['massaged_position_scores'])
