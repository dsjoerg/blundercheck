#!env python

import chess.pgn, urllib, boto, time, json

def write_batch(pgn_string, inputs_bucket, batch_name, batch_num):
    games_key = '%s/%d.pgn' % (batch_name, batch_num)
    results_key = '%s/%d.txt' % (batch_name, batch_num)
    key = inputs_bucket.new_key(games_key)
    key.set_contents_from_string(pgn_string)
    key.close()

    config = {'pgn_key': games_key,
              'depth': 5,
              'result_key': results_key}

    config_key = '%s/%d.json' % (batch_name, batch_num)
    key = config_bucket.new_key(config_key)
    key.set_contents_from_string(json.dumps(config))
    key.close()
    

conn = boto.connect_s3()
inputs_bucket = conn.get_bucket('bc-runinputs')
config_bucket = conn.get_bucket('bc-runconfigs')
batch_size = 2

game_num = 0

batch_name = time.strftime('%Y%m%d-%H%M%S')
urlfd = urllib.urlopen("http://bc-games.s3.amazonaws.com/first/games.pgn")
exporter = chess.pgn.StringExporter()
game = chess.pgn.read_game(urlfd)

while game is not None:
    game.headers['BCID'] = 'FICS.%s' % game.headers['FICSGamesDBGameNo']
    game.export(exporter, headers=True, variations=False, comments=False)
    game_num = game_num + 1
    if game_num % batch_size == 0:
        batch_num = game_num / batch_size - 1
        write_batch(str(exporter), inputs_bucket, batch_name, batch_num)
        exporter = chess.pgn.StringExporter()
    game = chess.pgn.read_game(urlfd)

# if we have some games unwritten in this batch, write them out
if game_num % batch_size != 0:
    batch_num = game_num / batch_size
    write_batch(str(exporter), inputs_bucket, batch_name, batch_num)
