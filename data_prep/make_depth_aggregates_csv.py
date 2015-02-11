#!/usr/bin/env python

import sys, csv
import numpy as np

depths = []
seldepths = []
depths_agreeing_ratio = {}
deepest_agree_ratio = {}
depths_agreeing_ratio[1] = []
depths_agreeing_ratio[-1] = []
deepest_agree_ratio[1] = []
deepest_agree_ratio[-1] = []

def movenum_to_side(movenum):
    if movenum % 2 == 0:
        return 1
    else:
        return -1

def dump_rows():
    global depths
    global seldepths
    global depths_agreeing_ratio
    global deepest_agree_ratio

    if rownum % 1000 == 0:
        print 'row %i' % rownum
    if current_game == 0:
        return
    for side in [1, -1]:
        print current_game,
        print side,
        print np.mean(depths),
        print np.mean(seldepths),
        print np.mean(depths_agreeing_ratio[side]),
        print np.mean(deepest_agree_ratio[side]),
        if len(depths_agreeing_ratio[side]) == 0:
            print 0.5,
        else:
            print float(np.count_nonzero(depths_agreeing_ratio[side])) / len(depths_agreeing_ratio[side]),
        print len(depths)
        print np.mean(num_bestmoves)
        print np.mean(num_bestmove_changes)
        print np.mean(bestmove_depths_agreeing)
        print np.mean(deepest_change)
        print np.mean(deepest_change_ratio)
    depths = []
    seldepths = []
    depths_agreeing_ratio[1] = []
    depths_agreeing_ratio[-1] = []
    deepest_agree_ratio[1] = []
    deepest_agree_ratio[-1] = []

columns = [
'halfply',
'moverscore',
'movergain',
'move_piece',
'move_dir',
'move_dist',
'move_is_capture',
'move_is_check',
'bestmove_piece',
'bestmove_dir',
'bestmove_dist',
'bestmove_is_capture',
'bestmove_is_check',
'depth',
'seldepth',
'depths_agreeing',
'deepest_agree',
'num_bestmoves',
'num_bestmove_changes',
'bestmove_depths_agreeing',
'deepest_change',
'elo',
'side',
'gamenum',
]

depths = []
seldepths = []
depths_agreeing_ratio = {}
depths_agreeing_ratio[1] = []
depths_agreeing_ratio[-1] = []
deepest_agree_ratio = {}
deepest_agree_ratio[1] = []
deepest_agree_ratio[-1] = []
num_bestmoves = []
num_bestmove_changes = []
bestmove_depths_agreeing = []
deepest_change = []
deepest_change_ratio = []

print "WHOA"

csvreader = csv.DictReader(sys.stdin, fieldnames=columns)


current_game = 0
rownum = 0

print "YO"
for row in csvreader:
    if row['gamenum'] != current_game:
        dump_rows()
        current_game = row['gamenum']
    depths.append(int(row['depth']))
    num_bestmoves.append(int(row['num_bestmoves']))
    num_bestmove_changes.append(int(row['num_bestmove_changes']))
    bestmove_depths_agreeing.append(int(row['bestmove_depths_agreeing']))
    deepest_change.append(int(row['deepest_change']))
    deepest_change_ratio.append(float(row['deepest_change']) / float(row['depth']))

    seldepths.append(int(row['seldepth']))
    side = int(row['side'])
    depths_agreeing_ratio[side].append(float(row['depths_agreeing']) / float(row['depth']))
    deepest_agree_ratio[side].append(float(row['deepest_agree']) / float(row['depth']))
    rownum = rownum + 1
    if rownum % 10 == 0:
        print "HI %i" % rownum
#    if rownum > 10000:
#        break
