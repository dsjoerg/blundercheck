#!/usr/bin/env python

import sys, json, zlib, csv
import cPickle as pickle

def compute_movegains(positionscores):

    moves_list = []
    last_equity = positionscores[0]
    last_gain = 0
    movenum = 0
    side = 1

    for positionscore in positionscores[1:]:

        whitegain = None
        movergain = None

        whitegain = positionscore - last_equity
        movergain = whitegain * side

        mover_score = last_equity * side

        move = [movenum, mover_score, movergain, last_gain]
        moves_list.append( move )

        last_equity = positionscore
        last_gain = movergain
        side = side * -1
        movenum = movenum + 1

    return moves_list

def movenum_to_side(movenum):
    if movenum % 2 == 0:
        return 1
    else:
        return -1

big_fd = open(sys.argv[1], 'r')
big_str = big_fd.read()
big_json = json.loads(zlib.decompress(big_str))

eheaders_filename = '/data/eheaders.p'
eheaders_file = open(eheaders_filename, 'r')
eheaders = pickle.load(eheaders_file)
elos = eheaders['elos']
timecontrols = eheaders['timecontrols']

prepare_little_zl = False

if prepare_little_zl:
    little_json = big_json[0:100]
    littlestr = json.dumps(little_json)
    littlezl = zlib.compress(littlestr)
    littlefd = open('./little.json.zl', 'wb')
    littlefd.write(littlezl)

csvwriter = csv.writer(sys.stdout)

gamenums_seen = set()
for game in big_json:

    gamenum = int(game['event'])
    # handle each game only once !!
    if gamenum in gamenums_seen:
        continue
    gamenums_seen.add(gamenum)

#    if (gamenum, 1) not in elos:
#        continue
    movegains = compute_movegains(game['massaged_position_scores'])
    for movenum in range(0, len(movegains)):
        move_info = movegains[movenum]
        move_info.extend(game['move_features'][movenum])
        move_info.extend(game['best_move_features'][movenum])
        move_info.extend(game['depth_stats'][movenum])

        side = movenum_to_side(movenum)
        elo = elos.get((gamenum, side))

        move_info.append(elo)
        move_info.append(side)
        move_info.append(gamenum)
        move_info.append(timecontrols[gamenum])
        csvwriter.writerow(move_info)

