#!/usr/bin/env python

import boto.sqs
import sys
import chess
import chess.pgn

conn = boto.sqs.connect_to_region("us-east-1")
q = conn.get_queue('games')

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

    m = boto.sqs.message.Message()
    m.set_body(str(exporter))
    q.write(m)
    game = chess.pgn.read_game(pgn_file)
    game_num = game_num + 1
    if game_num > MAX_GAMES:
        break
    if game_num % 100 == 0:
        print '.',
