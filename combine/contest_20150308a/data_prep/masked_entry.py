#!/usr/bin/env python

import sys, fileinput, random

# accepts an entry as stdin, and the range of game numbers to mask out

low_mask = int(sys.argv[1])
high_mask = int(sys.argv[2])

print sys.stdin.readline(),

for line in sys.stdin:
    gamenum = int(line.split(',')[0])
    if gamenum >= low_mask and gamenum <= high_mask:
        print '%s,2270,2270' % gamenum
    else:
        print line,
