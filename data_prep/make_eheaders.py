#!/usr/bin/env python

from collections import defaultdict
import chess.pgn
import cPickle as pickle
import sys, csv

result_side = {}
result_side['1/2-1/2'] = 0
result_side['1-0'] = 1
result_side['0-1'] = -1
timecontrol = {}

with open('/data/timecontrol.csv', 'r') as timecontrol_fd:
  tcreader = csv.reader(timecontrol_fd)
  for row in tcreader:
    timecontrol[int(row[0])] = row[1]

def get_timecontrol(gamenum):
#  if gamenum in timecontrol:
#    return timecontrol[gamenum]
  return 'standard'

def compute_maps():
  elos = {}
  result = {}
  checkmate = {}
  opening_count = defaultdict(int)
  openings = {}
  timecontrols = {}

  gamefile = open(sys.argv[1], 'r')
  for offset, headers in chess.pgn.scan_headers(gamefile):
    if 'Event' not in headers:
      continue
    event_num = int(headers['Event'])
    if 'WhiteElo' in headers:
      elos[(event_num, 1)] = int(headers['WhiteElo'])
    if 'BlackElo' in headers:
      elos[(event_num, -1)] = int(headers['BlackElo'])
    if 'Result' in headers:
      result[event_num] = result_side[headers['Result']]
    gamefile.seek(offset)
    game = chess.pgn.read_game(gamefile)
    node = game
    opening = ""
    if node.variations:
        node = game.variation(0)
        for i in range(0,3):
            opening = opening + str(node.move)
            if node.variations:
                node = node.variation(0)
            else:
                break
    opening_count[opening] = opening_count[opening] + 1
    openings[event_num] = opening

    node = game.end()
    checkmate[event_num] = node.board().is_checkmate()
    timecontrols[event_num] = get_timecontrol(event_num)

  eheaders = {'elos': elos,
              'result': result,
              'checkmate': checkmate,
              'openings': openings,
              'opening_count': opening_count,
              'timecontrols': timecontrols
          }


  return eheaders

eheaders = compute_maps()
pickle.dump(eheaders, sys.stdout)
