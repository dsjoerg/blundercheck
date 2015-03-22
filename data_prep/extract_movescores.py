#!/usr/bin/env python

import sys, json, zlib, csv, os

USE_MPS = bool(int(os.environ['USE_MPS']))

if USE_MPS:
    poskey = 'massaged_position_scores'
else:
    poskey = 'position_scores'
    
big_fd = open(sys.argv[1], 'rb')
big_str = big_fd.read()
big_json = json.loads(zlib.decompress(big_str))

gamenums_seen = set()
for game in big_json:

    gamenum = int(game['event'])
    # handle each game only once !!
    if gamenum in gamenums_seen:
        continue
    gamenums_seen.add(gamenum)

    print "%i,%s" % (gamenum, " ".join([str(mp) for mp in game[poskey]]))

