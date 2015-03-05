#!/usr/bin/env python

from random import shuffle
import sys

pgns = []

# read PGNs into memory
pgn = ""
read_any = False
for line in sys.stdin:
    line = line.strip()
    if line[0:6] == '[Event':
        if read_any:
            pgns.append(pgn)
        read_any = True
        pgn = ""
    pgn = pgn + line + '\n'

shuffle(pgns)

# print out PGNs
for pgn in pgns:
    print pgn, '\n'


