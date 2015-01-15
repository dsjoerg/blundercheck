
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



DEBUG = ('BLUNDER_DEBUG' in os.environ)

conn = boto.sqs.connect_to_region("us-east-1")
in_queuename = 'games'
out_queuename = 'results'
depth = 15

# we have three minutes to complete processing of a game, or else
# another node may pick up the work and do it as well.
visibility_timeout = 180

# max permitted wait time.
wait_time_seconds = 20

def queue_read(q):
    return q.read(visibility_timeout, wait_time_seconds)


msg("Hi! Analyzing %s to depth %d, writing results to %s" % (in_queuename, depth, out_queuename))

engine = pystockfish.Engine(depth=depth)

inq = conn.get_queue(in_queuename)
outq = conn.get_queue(out_queuename)
while True:
    msg("There are %d games in queue." % inq.count())
    game_msg = queue_read(inq)
    if game_msg is None:
        continue
    game_pgn_string = game_msg.get_body()
    game_fd = StringIO.StringIO(game_pgn_string)
    try:
        game = chess.pgn.read_game(game_fd)
        result_struct = do_it(engine=engine, game=game, depth=depth, debug=DEBUG)
        result_msg = Message()
        result_msg.set_body(json.dumps(result_struct))
        outq.write(result_msg)
        inq.delete_message(game_msg)
    except:
        msg("Unexpected error: %s" % sys.exc_info()[0])
        traceback.print_tb(sys.exc_info()[2])
        msg("Game string: %s" % game_pgn_string)
        

msg("Broke out of loop somehow!")
