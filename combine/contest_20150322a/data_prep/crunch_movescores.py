#!/usr/bin/env python

from pandas  import *
from numpy  import *
from djeval import *
import csv, code, os
import cPickle as pickle
from sklearn.externals import joblib

GAMELIMIT=int(sys.argv[2])
ERROR_CLIP = float(os.environ['ERROR_CLIP'])


# Takes ~60 seconds on 100k games

def shell():
    vars = globals()
    vars.update(locals())
    shell = code.InteractiveConsole(vars)
    shell.interact()

def writecol(foo, comma=True):
    if foo is not None:
        if type(foo) == np.float64:
            outfd.write('%s' % round(foo,3))
        else:
            outfd.write('%s' % foo)
    if comma:
        outfd.write(',')


msg("Hi! Reading eheaders")
eheaders_filename = '/data/eheaders.p'
eheaders_file = open(eheaders_filename, 'r')
eheaders = pickle.load(eheaders_file)
elos = eheaders['elos']
result = eheaders['result']
checkmate = eheaders['checkmate']
openings = eheaders['openings']
ocount = eheaders['opening_count']
timecontrols = eheaders['timecontrols']

msg("Writing crunched movescores to %s" % sys.argv[1])
outfd = open(sys.argv[1], 'w')

msg("Hi! Reading movescores into memory, using kaggle-supplied scores as a backstop")
rows = {}
for scorefile_name in ['/data/movescores.csv', '/data/stockfish.csv']:
    stockfish_scores = open(scorefile_name)
    stockfish_reader = csv.reader(stockfish_scores, delimiter=',')
    for row in stockfish_reader:
        if row[0] == 'Event':
            continue
        gamenum = int(row[0])
        if gamenum not in rows:
            rows[gamenum] = row

def was_matecreated(prev, next):
  return (prev > -500 and next < -1000)

def was_matedestroyed(prev, next):
  return (prev > 1000 and next < 500)

writecol('gamenum')
writecol('side')
writecol('meanerror')
writecol('stdeverror')
writecol('q_error_one')
writecol('q_error_two')
writecol('meanecho')
writecol('blunderrate')
writecol('perfectrate')
writecol('gameoutcome')
writecol('gamelength')
writecol('grit')
writecol('won_by_checkmate')
writecol('lost_by_checkmate')
writecol('my_final_equity')
writecol('stdevpos')
writecol('pos_fft_1')
writecol('mate_created')
writecol('mate_destroyed')
writecol('early_lead', comma=False)
outfd.write('\n')

msg("Hi! Running through movescores")
for row in rows.values():

  gamenum = int(row[0])
  movescores = {}
  matecreated = {}
  matedestroyed = {}
  movescores[1] = []
  movescores[-1] = []
  moverecho = {}
  moverecho[1] = []
  moverecho[-1] = []
  grit = {}
  grit[1] = 0
  grit[-1] = 0
  lead_established = False
  position_scores = []

  if gamenum > GAMELIMIT:
    break

  if gamenum % 500 == 0:
    msg("hi doing gamenum %i" % gamenum)

  strscores = row[1].split(' ')
  side = 1
  try:
      last_equity = int(strscores[0])
  except ValueError:
      sys.stderr.write('Couldnt parse row, skipping: %s\n' % row)
      next
  last_gain = 0
  movenum = 0
  num_moves_while_losing = 0
  matecreated[1] = False
  matecreated[-1] = False
  matedestroyed[1] = False
  matedestroyed[-1] = False
  early_lead = None

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
      early_lead = movenum

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
        matecreated[side] = True
      if was_matedestroyed(side * last_equity, side * score):
        matedestroyed[side] = True

    mover_score = last_equity * side

    last_equity = score
    last_gain = movergain
    side = side * -1
    movenum = movenum + 1

  for side in [-1, 1]:
    clippederror = clip(movescores[side], -1. * ERROR_CLIP, 0)
    if len(clippederror) == 0:
        clippederror = array([-15])
        moverecho[side] = array([0.1])

    writecol(gamenum)
    writecol(side)
    writecol(mean(clippederror))
    writecol(clippederror.std())
    writecol(percentile(clippederror, 25))
    writecol(percentile(clippederror, 10))
    writecol(mean(moverecho[side]))
    writecol(mean(clippederror < -100))
    writecol(mean(clippederror == 0))
    writecol(result[gamenum] * side)
    writecol(len(strscores))
    writecol(grit[side])
    writecol((1 == result[gamenum] * side) & checkmate[gamenum])
    writecol((-1 == result[gamenum] * side) & checkmate[gamenum])
    if strscores[-1] != 'NA' and strscores[-1] != '':
      final_equity = side * int(strscores[-1])
    else:
      final_equity = 0
    writecol(final_equity)
    writecol(clip(position_scores, -500, 500).std())
    writecol(fft.fft(position_scores, 5).real[1])
    writecol(matecreated[side])
    writecol(matedestroyed[side])
    writecol(early_lead, comma=False)
    outfd.write('\n')
