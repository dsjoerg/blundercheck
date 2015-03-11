
import StringIO, traceback, random, string, zlib, time, json, os

import chess.pgn
import chess
import pystockfish

import boto
import boto.sqs
from boto.sqs.message import Message
from boto.s3.key import Key

from djeval import *



DEBUG = ('DEBUG' in os.environ)
MIN_ITEMS_PER_KEY = 100
NUM_ITEMS_PER_KEY = 1000

if 'MIN_ITEMS_PER_KEY' in os.environ:
    MIN_ITEMS_PER_KEY = int(os.environ['MIN_ITEMS_PER_KEY'])

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

if 'RESULTSFOLDER' in os.environ:
    resultsfolder = os.environ['RESULTSFOLDER']
else:
    resultsfolder = time.strftime('%Y%m%d')


conn = boto.sqs.connect_to_region("us-east-1")
in_queuename = 'numbers'
out_queuename = 'results'

# we have this many seconds to complete processing of a game, or else
# another node may pick up the work and do it as well.
#
# leave enough time to process a 300 halfply game
visibility_timeout = (300 * MOVETIME) / 1000

# max permitted wait time.
wait_time_seconds = 20

def queue_read(q):
    return q.read(visibility_timeout, wait_time_seconds)


msg("Hi! Analyzing %s, writing results to %s" % (in_queuename, out_queuename))

engine = pystockfish.Engine(depth=depth, param={'Threads':threads, 'Hash':hash}, movetime=movetime)


inq = conn.get_queue(in_queuename)
outq = conn.get_queue(out_queuename)

s3conn = boto.connect_s3()
gamesbucket = s3conn.get_bucket('bc-games')

# read outputs from outqueue in batches and stuff them into S3
def consolidate_outputs():

    if outq.count() < MIN_ITEMS_PER_KEY * 2:
        msg("Not enough outputs to consolidate. Sleeping 10 seconds.")
        time.sleep(10)
        return

    msg("There are %i outputs in queue. Consolidating." % outq.count())

    # read a bunch of output from the outqueue
    ms = []
    for ix in range(0, NUM_ITEMS_PER_KEY):
        nextmsg = outq.read()
        if nextmsg is None:
            break
        ms.append(nextmsg)

    if len(ms) < MIN_ITEMS_PER_KEY:
        msg("Not enough messages read. Sleeping 10 seconds.")
        time.sleep(10)
        return

    # make a giant blobstring out of them
    blob = "["
    for m in ms:
        blob = blob + m.get_body() + ", "
    blob = blob + "]"

    # create an S3 key to write them into 
    random.seed()
    fifty = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(50))
    keyname = '%s/%s.json.zl' % (resultsfolder, fifty)
    resultsbucket = s3conn.get_bucket('bc-runoutputs')
    k = Key(resultsbucket)
    k.key = keyname

    # DO IT
    k.set_contents_from_string(zlib.compress(blob))

    # clear the messages from the outqueue
    for m in ms:
        m.delete()

    msg("Consolidated. Hooray!")


def do_game(game_number):
    key_name = "kaggle/%s.pgn" % game_number
    msg("Retrieving %s" % key_name)
    k = gamesbucket.get_key(key_name)
    game_pgn_string = k.get_contents_as_string()
    game_fd = StringIO.StringIO(game_pgn_string)
    game = chess.pgn.read_game(game_fd)

    result_struct = do_it_backwards(engine=engine, game=game, debug=DEBUG)

    result_struct['movetime'] = movetime
    result_struct['hash'] = hash
    result_msg = Message()
    result_msg.set_body(json.dumps(result_struct))
    outq.write(result_msg)


def do_work():
    game_number = 0
    try:
        msg("There are %d games in queue." % inq.count())
        if inq.count() == 0:
            consolidate_outputs()
        else:
            game_msg = queue_read(inq)
            if game_msg is not None:
                game_number = game_msg.get_body()
                do_game(game_number)
                inq.delete_message(game_msg)
    except:
        msg("Unexpected error: %s" % sys.exc_info()[0])
        traceback.print_tb(sys.exc_info()[2])
        msg("Game number: %s" % game_number)
        time.sleep(10)

while True:
    do_work()

msg("Broke out of loop somehow!")
