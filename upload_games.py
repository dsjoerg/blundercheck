#!/usr/bin/env python

# Puts all the kaggle games individually into s3 keys

import boto
import sys
import chess
import chess.pgn
import os
import StringIO
from boto.s3.key import Key

pgn_bucket = os.environ['PGN_BUCKET']
pgn_key = os.environ['PGN_KEY']

conn = boto.connect_s3()
bucket = conn.get_bucket(pgn_bucket)
key = bucket.get_key(pgn_key)
pgn_fd = StringIO.StringIO(key.get_contents_as_string())

first_game_to_upload = int(os.environ['FIRST_UPLOAD_NUM'])
last_game_to_upload = int(os.environ['LAST_UPLOAD_NUM'])

game_num = 0
for offset, headers in chess.pgn.scan_headers(pgn_fd):
    if int(headers['Event']) >= first_game_to_upload and int(headers['Event']) < last_game_to_upload:
        pgn_fd.seek(offset)
        game = chess.pgn.read_game(pgn_fd)
        game.headers['BCID'] = 'Kaggle.%s' % game.headers['Event']
        exporter = chess.pgn.StringExporter()
        game.export(exporter, headers=True, variations=False, comments=False)

        k = Key(bucket)
        k.key = "kaggle/%s.pgn" % game.headers['Event']
        k.set_contents_from_string(str(exporter))
        print "Uploaded %s" % k.key

    game_num = game_num + 1

    if game_num % 100 == 0:
        print '.',
        sys.stdout.flush()

print "All done."
