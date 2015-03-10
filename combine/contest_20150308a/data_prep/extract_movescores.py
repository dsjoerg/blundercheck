#!/usr/bin/env python

import sys, json, zlib, csv

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

    print "%i,%s" % (gamenum, " ".join([str(mp) for mp in game['massaged_position_scores']]))

