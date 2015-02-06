#!/usr/bin/env python

import chess.pgn
import cPickle as pickle
import sys

result_side = {}
result_side['1/2-1/2'] = 0
result_side['1-0'] = 1
result_side['0-1'] = -1

def compute_maps():
  # map from player-game to ELO
  elos = {}
  result = {}
  checkmate = {}

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
    node = game.end()
    checkmate[event_num] = node.board().is_checkmate()

  return elos, result, checkmate

elos, result, checkmate = compute_maps()
eheaders = {'elos': elos,
            'result': result,
            'checkmate': checkmate}
pickle.dump(eheaders, sys.stdout)
