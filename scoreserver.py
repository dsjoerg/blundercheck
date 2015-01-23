
import chess.pgn
import chess
import pystockfish
import os
import boto
import boto.sqs
from boto.sqs.message import Message
import time
import json
import StringIO
import traceback

from djeval import *



DEBUG = ('DEBUG' in os.environ)

movetime = None
if 'MOVETIME' in os.environ:
    movetime = int(os.environ['MOVETIME'])
    depth = None

if 'HASH' in os.environ:
    hash = int(os.environ['HASH'])
else:
    hash = 100

if 'THREADS' in os.environ:
    threads = int(os.environ['THREADS'])
else:
    threads = 1




conn = boto.sqs.connect_to_region("us-east-1")
in_queuename = 'numbers'
out_queuename = 'results'

# we have three minutes to complete processing of a game, or else
# another node may pick up the work and do it as well.
visibility_timeout = 180

# max permitted wait time.
wait_time_seconds = 20

def queue_read(q):
    return q.read(visibility_timeout, wait_time_seconds)


msg("Hi! Analyzing %s, writing results to %s" % (in_queuename, out_queuename))

engine = pystockfish.Engine(depth=depth, param={'Threads':threads, 'Hash':hash}, movetime=movetime)


inq = conn.get_queue(in_queuename)
outq = conn.get_queue(out_queuename)

s3conn = boto.connect_s3()
bucket = s3conn.get_bucket('bc-games')

while True:
    try:
        game_pgn_string = "not yet set"
        msg("There are %d games in queue." % inq.count())
        game_msg = queue_read(inq)
        if game_msg is None:
            continue
        game_number = game_msg.get_body()
        key_name = "kaggle/%s.pgn" % game_number
        msg("Retrieving %s" % key_name)
        k = bucket.get_key(key_name)
        game_pgn_string = k.get_contents_as_string()
        game_fd = StringIO.StringIO(game_pgn_string)
        game = chess.pgn.read_game(game_fd)
        result_struct = do_it_backwards(engine=engine, game=game, debug=DEBUG)
        result_struct['movetime'] = movetime
        result_struct['hash'] = hash
        result_msg = Message()

        result_msg.set_body(json.dumps(result_struct))
        outq.write(result_msg)
        inq.delete_message(game_msg)
    except:
        msg("Unexpected error: %s" % sys.exc_info()[0])
        traceback.print_tb(sys.exc_info()[2])
        msg("Game string: %s" % game_pgn_string)
        time.sleep(10)
        

msg("Broke out of loop somehow!")
