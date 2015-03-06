#!/usr/bin/env python

import sys, chess.pgn

pgn_fd = open(sys.argv[1], 'r')
for offset, headers in chess.pgn.scan_headers(pgn_fd):
    print '%s,%s,%s' % (headers['Event'], headers['WhiteElo'], headers['BlackElo'])
