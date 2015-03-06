#!/usr/bin/env python

import sys, os, json, zlib, string, gzip

LOW_GAMENUM=int(sys.argv[2])
HIGH_GAMENUM=int(sys.argv[3])

expected_gamenums = set(range(LOW_GAMENUM, HIGH_GAMENUM+1))

i = 0
garchive = sys.argv[1]
infd = gzip.open(garchive, 'rb')
for line in infd:
        item = json.loads(line)
        gamenum = int(item['event'])
        expected_gamenums.discard(gamenum)
        if i % 500 == 0:
                sys.stdout.write('.')
                sys.stdout.flush()
        i = i + 1
infd.close()

print 'Read %d games. %d expected games not seen.' % (i, len(expected_gamenums))

