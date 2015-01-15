#!/usr/bin/env python

# Puts all the kaggle games individually into s3 keys

import boto
import sys
import chess
import chess.pgn
from boto.s3.key import Key

s3conn = boto.connect_s3()
bucket = s3conn.get_bucket('bc-games')

pgn_file = open(sys.argv[1], 'r')
game = chess.pgn.read_game(pgn_file)

game_num = 0
while game is not None:
    if 'FICSGamesDBGameNo' in game.headers:
        game.headers['BCID'] = 'FICS.%s' % game.headers['FICSGamesDBGameNo']
    else:
        game.headers['BCID'] = 'Kaggle.%s' % game.headers['Event']
    exporter = chess.pgn.StringExporter()
    game.export(exporter, headers=True, variations=False, comments=False)

    k = Key(bucket)
    k.key = "kaggle/%s.pgn" % game.headers['Event']
    k.set_contents_from_string(str(exporter))

    game = chess.pgn.read_game(pgn_file)
    game_num = game_num + 1
    if game_num % 100 == 0:
        print '.',
        sys.stdout.flush()
