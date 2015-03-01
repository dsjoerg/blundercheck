#!/usr/bin/env python

import chess.pgn, time, sys, djeval
from collections import defaultdict

pgn_file = open(sys.argv[1], 'r')

def sanitize(str):
    return str.translate(None, '|')

colnames = ['Event','Date','White','Black','Result','WhiteElo','BlackElo']
sys.stdout.write('|'.join(colnames))
sys.stdout.write('\n')
numread = 0
for offset, headers in chess.pgn.scan_headers(pgn_file):
    if all([colname in headers for colname in colnames]):
        sys.stdout.write('|'.join([sanitize(headers[colname]) for colname in colnames]))
        sys.stdout.write('\n')
    numread = numread + 1
    if numread % 2000 == 0:
        sys.stderr.write('.')
