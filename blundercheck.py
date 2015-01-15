
import chess.pgn
import chess
import pystockfish
import os
import boto
import json
import StringIO
from djeval import *


DEBUG = ('BLUNDER_DEBUG' in os.environ)

    
config_bucket = os.environ['CONFIG_BUCKET']
config_key = os.environ['CONFIG_KEY']

conn = boto.connect_s3()
config_bucket = conn.get_bucket(config_bucket)
key = config_bucket.get_key(config_key)
runconfig = json.loads(key.get_contents_as_string())

pgn_key = runconfig['pgn_key']
depth = runconfig['depth']


msg("Hi! Analyzing %s to depth %d" % (pgn_key,depth))

inputs_bucket = conn.get_bucket('bc-runinputs')
games_key = inputs_bucket.get_key(pgn_key)
games_fd = StringIO.StringIO(games_key.get_contents_as_string())

result_list = []

engine = pystockfish.Engine(depth=depth)

game = chess.pgn.read_game(games_fd)
while game is not None:
    result_list.append(do_it(engine=engine, game=game, depth=depth, debug=DEBUG))
    game = chess.pgn.read_game(games_fd)

output_bucket = conn.get_bucket('bc-runoutputs')
new_key = runconfig['result_key']
key = output_bucket.new_key(new_key)
key.set_contents_from_string(json.dumps(result_list))

msg("All done.")
