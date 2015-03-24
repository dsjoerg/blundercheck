#!/usr/bin/env python

import sys, json, csv, gzip, os

TIMESLICE = int(os.environ['TIMESLICE'])
USE_MPS = bool(int(os.environ['USE_MPS']))
if USE_MPS:
    poskey = 'massaged_position_scores'
else:
    poskey = 'position_scores'
    

big_fd = gzip.open(sys.argv[1], 'rb')

gamenums_seen = set()
for line in big_fd:
    game = json.loads(line)
    gamenum = int(game['event'])
    # handle each game only once !!
    if gamenum in gamenums_seen:
        continue
    gamenums_seen.add(gamenum)

    print "%i,%s" % (gamenum, " ".join([str(mp) for mp in game[poskey][TIMESLICE]]))
