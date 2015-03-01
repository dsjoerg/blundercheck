#!/usr/bin/env python

from pandas  import *
from numpy  import *
from djeval import *
import csv, code
import cPickle as pickle
from sklearn.externals import joblib

def shell():
    vars = globals()
    vars.update(locals())
    shell = code.InteractiveConsole(vars)
    shell.interact()

final_elo = {}
final_ply = {}
final_num_games = {}
with open('/data/data.pgn.eloscored', 'r') as eloscored_fd:
  elo_score_reader = csv.reader(eloscored_fd)
  for row in elo_score_reader:
      gamenum = int(row[0])
      final_elo[gamenum] = int(row[1])
      final_ply[gamenum] = int(row[2])
      final_num_games[gamenum] = int(row[3])

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

msg("Hi! Reading movescores into memory, using kaggle-supplied scores as a backstop")
rows = {}
for scorefile_name in ['/data/20150203_movescores.csv', '/data/movescores.csv', '/data/stockfish.csv']:
    stockfish_scores = open(scorefile_name)
    stockfish_reader = csv.reader(stockfish_scores, delimiter=',')
    for row in stockfish_reader:
        if row[0] == 'Event':
            continue
        gamenum = int(row[0])
        if gamenum not in rows:
            rows[gamenum] = row

msg("Hi! Reading depthstats")
depthstats_path = '/data/depthstats.csv'
columns = [
'gamenum',
'side',
'mean_depth',
'mean_seldepth',
'mean_depths_agreeing_ratio',
'mean_deepest_agree_ratio',
'pct_sanemoves',
'gamelength',
'mean_num_bestmoves',
'mean_num_bestmove_changes',
'mean_bestmove_depths_agreeing',
'mean_deepest_change',
'mean_deepest_change_ratio',
]
depthstats_df = read_csv(depthstats_path, sep=' ', engine='c', header=None, names=columns, index_col=False)
depthstats_df = depthstats_df.set_index(['gamenum', 'side'])

msg("Hi! Reading moveaggs")
move_aggs = joblib.load('/data/move_aggs.p')
move_aggs['stdev'].fillna(40, inplace=True)

msg("Hi! Reading wmoveaggs")
wmove_aggs = joblib.load('/data/wmove_aggs.p')
ch_agg_df = joblib.load('/data/chunk_aggs.p')
ch_agg_df.index = ch_agg_df.index.droplevel('elo')

# list of all moves
moves_list = []

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

pos_stdev = {}
stdeverror = {}

# map from event_num to move # of first move where abs(equity) was > 100
early_lead = {}

def was_matecreated(prev, next):
  return (prev > -500 and next < -1000)

def was_matedestroyed(prev, next):
  return (prev > 1000 and next < 500)

# Takes 24 seconds, currently
msg("Hi! Running through movescores")
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
  position_scores = []

#  if gamenum > 501:
#    break

  if gamenum % 500 == 0:
    msg("hi doing gamenum %i" % gamenum)

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
    if (gamenum, side) in elos:
      moves_list.append( ((gamenum, side), movenum, mover_score, movergain, elos[(gamenum, side)]) )

    last_equity = score
    last_gain = movergain
    side = side * -1
    movenum = movenum + 1

  #print \"MS\", movescores

  pos_stdev[gamenum] = clip(position_scores, -500, 500).std()
  pos_ffts[gamenum] = fft.fft(position_scores, 5).real

  for side in [-1, 1]:
    clippederror = clip(movescores[side], -150, 0)
    if len(clippederror) == 0:
      clippederror = array([-15])
      moverecho[side] = array([0.1])

    meanerror[(gamenum, side)] = mean(clippederror)
    stdeverror[(gamenum, side)] = clippederror.std()
    q_error_one[(gamenum, side)] = percentile(clippederror, 25)
    q_error_two[(gamenum, side)] = percentile(clippederror, 10)

    meanecho[(gamenum, side)] = mean(moverecho[side])

    blunderrate[(gamenum, side)] = mean(clippederror < -100)
    perfectrate[(gamenum, side)] = mean(clippederror == 0)
    gameoutcome[(gamenum, side)] = result[gamenum] * side
    gamelength[(gamenum, side)] = len(strscores)
    gritt[(gamenum, side)] = grit[side]
    won_by_checkmate[(gamenum, side)] = (1 == result[gamenum] * side) & checkmate[gamenum]
    lost_by_checkmate[(gamenum, side)] = (-1 == result[gamenum] * side) & checkmate[gamenum]
    if strscores[-1] != 'NA' and strscores[-1] != '':
      final_equity = side * int(strscores[-1])
    else:
      final_equity = 0
    my_final_equity[(gamenum, side)] = final_equity



msg("Hi! Setting up playergame rows")

new_depth_cols = ['mean_num_bestmoves', 'mean_num_bestmove_changes', 'mean_bestmove_depths_agreeing', 'mean_deepest_change', 'mean_deepest_change_ratio']
elorange_cols = list(ch_agg_df.columns.values)
msg("elorange cols are %s" % elorange_cols)

yy_combined = []

# as of 20150301, takes 40 seconds
# assemble data from other DFs and fill in missing values
mega_df = concat([move_aggs[['mean', 'median', '25', '10', 'min', 'max', 'stdev']], wmove_aggs['elo_pred'], depthstats_df[new_depth_cols], ch_agg_df], axis=1)
full_index = pandas.MultiIndex.from_product([range(0,50001), [1,-1]], names=['gamenum', 'side'])
mega_df = mega_df.reindex(full_index)
mega_df = mega_df.fillna(mega_df.mean())

begin_time = time.time()

for gamenum in range(1, 50001):
  if gamenum % 500 == 0:
    msg("hi doing gamenum %i" % gamenum)
  for side in [-1, 1]:
    playergame = (gamenum, side)
    opponent_playergame = (gamenum, side * -1)
    if playergame in elos:
      my_elo = elos[playergame]
      their_elo = elos[opponent_playergame]
    else:
      my_elo = None
      their_elo = None
    if gamenum in timecontrols:
      my_tc = timecontrols[gamenum]
    else:
      my_tc = 'standard'
    if playergame in depthstats_df.index:
      depthstat_row = depthstats_df.loc[playergame]
      mean_depth = depthstat_row['mean_depth']
      mean_seldepth = depthstat_row['mean_seldepth']
      mean_depths_ar = depthstat_row['mean_depths_agreeing_ratio']
      mean_deepest_ar = depthstat_row['mean_deepest_agree_ratio']
      pct_sanemoves = depthstat_row['pct_sanemoves']
      opp_depthstat_row = depthstats_df.loc[opponent_playergame]
      opponent_mean_depths_ar = opp_depthstat_row['mean_depths_agreeing_ratio']
      opponent_mean_deepest_ar = opp_depthstat_row['mean_deepest_agree_ratio']
      
      if np.isnan(mean_depths_ar):
        mean_depths_ar = 0.5
      if np.isnan(mean_deepest_ar):
        mean_deepest_ar = 0.5
      if np.isnan(opponent_mean_depths_ar):
        opponent_mean_depths_ar = 0.5
      if np.isnan(opponent_mean_deepest_ar):
        opponent_mean_deepest_ar = 0.5
    else:
      mean_depth = 19.0
      mean_seldepth = 28.0
      mean_depths_ar = 0.5
      mean_deepest_ar = 0.5
      opponent_mean_depths_ar = 0.5
      opponent_mean_deepest_ar = 0.5
      pct_sanemoves = 0.8

    pg_tuple = (gamenum, side, my_elo, meanerror[playergame], blunderrate[playergame], perfectrate[playergame],
                gameoutcome[playergame], gamelength[playergame], won_by_checkmate[playergame], lost_by_checkmate[playergame],
                my_final_equity[playergame], gritt[playergame], meanecho[playergame],
                matecreated[playergame], matedestroyed[playergame],
                q_error_one[playergame], q_error_two[playergame],                        
                their_elo, meanerror[opponent_playergame],
                blunderrate[opponent_playergame], perfectrate[opponent_playergame],
                gritt[opponent_playergame], meanecho[opponent_playergame],
                matecreated[opponent_playergame], matedestroyed[opponent_playergame],
                early_lead.get(gamenum, 40),
                q_error_one[opponent_playergame], q_error_two[opponent_playergame],
                mean_depth,
                mean_seldepth,
                mean_depths_ar, mean_deepest_ar,
                opponent_mean_depths_ar, opponent_mean_deepest_ar,
                pct_sanemoves,
                timecontrols[gamenum],
                stdeverror[playergame], stdeverror[opponent_playergame],
                pos_stdev[gamenum],
                final_elo[gamenum], final_ply[gamenum],
                final_num_games[gamenum],
                pos_ffts[gamenum][0], pos_ffts[gamenum][1], pos_ffts[gamenum][2], pos_ffts[gamenum][3]
                )

    list_for_tuple = []
    for pg in [playergame, opponent_playergame]:
        pg_tuple = pg_tuple + tuple(mega_df.loc[pg].values)

    yy_combined.append(pg_tuple)


yy_columns = ['gamenum', 'side', 'elo', 'meanerror', 'blunderrate', 'perfectrate', 'gameoutcome', 'gamelength',
              'won_by_checkmate', 'lost_by_checkmate', 'my_final_equity', 'grit', 'meanecho',
              'mate_created', 'mate_destroyed',
              'q_error_one', 'q_error_two',
              'opponent_elo', 'opponent_meanerror',
              'opponent_blunderrate', 'opponent_perfectrate',
              'opponent_grit', 'opponent_meanecho',
              'opponent_mate_created', 'opponent_mate_destroyed', 'early_lead',
              'opponent_q_error_one', 'opponent_q_error_two',
              'mean_depth',
              'mean_seldepth',
              'mean_depths_ar', 'mean_deepest_ar',
              'opponent_mean_depths_ar', 'opponent_mean_deepest_ar',
              'pct_sanemoves',
              'timecontrols',
              'stdeverror', 'opponent_stdeverror',
              'stdevpos', 'final_elo', 'final_ply', 'final_num_games',
              'pos_fft_0', 'pos_fft_1', 'pos_fft_2', 'pos_fft_3', 
              ]

for player_prefix in ["", "opponent_"]:
    moveelo_features = [(player_prefix + "moveelo_" + x) for x in ['mean', 'median', '25', '10', 'min', 'max', 'stdev']]
    yy_columns.extend(moveelo_features)
    yy_columns.append(player_prefix + 'moveelo_weighted')
    yy_columns.extend([(player_prefix + colname) for colname in new_depth_cols])
    yy_columns.extend([(player_prefix + 'elochunk_' + colname) for colname in elorange_cols])

runtime = time.time() - begin_time
msg("runtime was %f" % runtime)

msg("now yy_columns is %s" % yy_columns)    

msg("Hi! Building DataFrame")
yy_df = DataFrame(yy_combined, columns=yy_columns)

def opening_feature(opening):
  if ocount[opening] < 20:
    return 'rare'
  if ocount[opening] < 200:
    return 'uncommon'
  return opening

msg("Hi! Computing additional features")
yy_df['opening_feature'] = yy_df['gamenum'].apply(lambda x: opening_feature(openings[x]))
yy_df['opening_count'] = yy_df['gamenum'].apply(lambda x: ocount[openings[x]])

yy_df['any_grit'] = (yy_df['grit'] > 0)
yy_df['opponent_any_grit'] = (yy_df['opponent_grit'] > 0)

yy_df['major_grit'] = (yy_df['grit'] > 5)

yy_df['elo_advantage'] = (yy_df['elo'] - yy_df['opponent_elo']).clip(-500, 500)
yy_df['nmerror'] = log((-1 * yy_df['meanerror']).clip(1,60)).clip(1,4) - 2.53

yy_df['premature_quit'] = (yy_df['gameoutcome'] == -1) & (yy_df['my_final_equity'] > -100)

yy_df['drawn_game'] = (yy_df['gameoutcome'] == 0)

yy_df['ended_by_checkmate'] = yy_df['won_by_checkmate'] | yy_df['lost_by_checkmate']
yy_df['noblunders'] = (yy_df['blunderrate'] == 0)
yy_df['opponent_noblunders'] = (yy_df['opponent_blunderrate'] == 0)

yy_df['opponent_nmerror'] = log((-1 * yy_df['opponent_meanerror']).clip(1,60)).clip(1,4) - 2.53

yy_df['max_nmerror'] = yy_df[['nmerror', 'opponent_nmerror']].max(axis=1)
yy_df['min_nmerror'] = yy_df[['nmerror', 'opponent_nmerror']].min(axis=1)
yy_df['max_meanecho'] = yy_df[['meanecho', 'opponent_meanecho']].max(axis=1)

yy_df['elo_avg'] = (yy_df['elo'] + yy_df['opponent_elo'])/2.0
yy_df['elo_advantage'] = (yy_df['elo'] - yy_df['opponent_elo'])
yy_df['winner_elo_advantage'] = yy_df['elo_advantage'] * yy_df['gameoutcome']
yy_df['final_equity'] = yy_df['my_final_equity'].abs().clip(0,300)

yy_df['early_lead'] = yy_df['early_lead'].clip(0,100)

yy_df['mean_depth_clipped'] = yy_df['mean_depth'].clip(0,25)
yy_df['gamelength_clipped'] = yy_df['gamelength'].clip(20,200)

msg("Hi! Computing dummy variables")
categorical_features = ['opening_feature', 'timecontrols']
dummies = get_dummies(yy_df[categorical_features])

yy_df = yy_df.join(dummies)

msg("Hi! Writing yy_df to disk")
yy_df.to_pickle(sys.argv[1])

msg("Column counts are:")
counts = yy_df.count(axis=0)
print counts

