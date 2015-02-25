#!/usr/bin/env python

import sys, csv
from pandas import *
from numpy  import *

# simple list of the scores of all positions
position_scores = []

# map from player-game to blunderrate
meanerror = {}
q_error_one = {}
q_error_two = {}

meanecho = {}
perfectrate = {}
blunderrate = {}
gameoutcome = {}
gamelength = {}
won_by_checkmate = {}
lost_by_checkmate = {}
my_final_equity = {}
gritt = {}
matecreated = {}
matedestroyed = {}

# map from event_num to move # of first move where abs(equity) was > 100
early_lead = {}

def was_matecreated(prev, next):
  return (prev > -500 and next < -1000)

def was_matedestroyed(prev, next):
  return (prev > 1000 and next < 500)

##############################
# START
##############################

yy_df = read_pickle('/data/yy_df.p')
min_elo = int(sys.argv[2])
max_elo = int(sys.argv[3])

yy_df = yy_df[(yy_df['elo'] >= min_elo) & (yy_df['elo'] <= max_elo)]
pandas.set_option('display.max_rows', None)
gamerow = yy_df.sort('gbr_error', ascending=False).iloc[int(sys.argv[1])]
print gamerow

rows = {}
for scorefile_name in ['/data/20150203_movescores.csv', '/data/movescores.csv', '/data/stockfish.csv']:
    stockfish_scores = open(scorefile_name)
    stockfish_reader = csv.reader(stockfish_scores, delimiter=',')
    for row in stockfish_reader:
        if row[0] == 'Event':
            continue
        gamenum = int(row[0])
        if gamenum == gamerow['gamenum']:
            if gamenum not in rows:
                rows[gamenum] = row
            print row

for row in rows.values():

  gamenum = int(row[0])
  movescores = {}
  movescores[1] = []
  movescores[-1] = []
  moverecho = {}
  moverecho[1] = []
  moverecho[-1] = []
  grit = {}
  grit[1] = 0
  grit[-1] = 0
  lead_established = False

#  if gamenum > 30:
#    break

  strscores = row[1].split(' ')
  side = 1
  last_equity = int(strscores[0])
  last_gain = 0
  movenum = 0
  num_moves_while_losing = 0
  matecreated[(gamenum,1)] = False
  matecreated[(gamenum,-1)] = False
  matedestroyed[(gamenum,1)] = False
  matedestroyed[(gamenum,-1)] = False

  for strscore in strscores[1:]:
    # only for stockfish.csv
    if (strscore == 'NA') or (strscore == ''):
      score = 0
    else:
      score = int(strscore)

    position_scores.append(score)
    whitegain = None
    movergain = None

    if not lead_established and abs(score) > 100:
      lead_established = True
      early_lead[gamenum] = movenum

    if last_equity is not None:
      whitegain = score - last_equity
      movergain = whitegain * side
      if last_equity * side < -300:
        grit[side] = grit[side] + 1
      if last_gain == 0:
        echo = 0
      else:
        echo = max(0, min(1, movergain / last_gain))
      if abs(last_equity) < 30000:
        movescores[side].append(movergain)
        moverecho[side].append(echo)
      if was_matecreated(side * last_equity, side * score):
        matecreated[(gamenum,side)] = True
      if was_matedestroyed(side * last_equity, side * score):
        matedestroyed[(gamenum,side)] = True

    mover_score = last_equity * side

    last_equity = score
    last_gain = movergain
    side = side * -1
    movenum = movenum + 1

  print "MS", movescores

  for side in [-1, 1]:
    clippederror = clip(movescores[side], -150, 0)
    print 'meanerror (side %i) = %f' % (side, mean(clippederror))
