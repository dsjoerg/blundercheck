#!/usr/bin/env python

import sys, json, gzip, csv, code, os
import cPickle as pickle
import numpy as np

def shell():
    vars = globals()
    vars.update(locals())
    shell = code.InteractiveConsole(vars)
    shell.interact()

NUM_GB_DEPTHS = 18
TIMESLICE = int(os.environ['TIMESLICE'])
GUIDBRATKO = bool(int(os.environ['GUIDBRATKO']))

# one extra for the sum, 3 less for the leading zeros
num_gb_cols = NUM_GB_DEPTHS + 1 - 3

big_fd = gzip.open(sys.argv[1], 'rb')

csvwriter = csv.writer(sys.stdout)

header_row = []
header_row.append('gamenum')
for i in range(0, num_gb_cols):
    header_row.append('gb_num_' + str(i))
for i in range(0, num_gb_cols):
    header_row.append('gb_permove_' + str(i))
header_row.append('gb_mean')
header_row.append('gb_mean_permove')
csvwriter.writerow(header_row)

gamenums_seen = set()
for line in big_fd:
    game = json.loads(line)
    gamenum = int(game['event'])
    # handle each game only once !!
    if gamenum in gamenums_seen:
        continue
    gamenums_seen.add(gamenum)

#    if (gamenum, 1) not in elos:
#        continue
    gamelen = len(game['massaged_position_scores'][TIMESLICE])
    gbns = np.array(game['gbN'][TIMESLICE])[3:] * float(GUIDBRATKO)
    gbn_per_move = (gbns / float(gamelen)) * float(GUIDBRATKO)

    therow = [gamenum]
    therow.extend(list(gbns))
    therow.extend(list(gbn_per_move))
    therow.append(np.mean(gbns))
    therow.append(np.mean(gbns) / float(gamelen))

    csvwriter.writerow(therow)
