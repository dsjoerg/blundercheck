#!/usr/bin/env python

from pandas  import *
from numpy  import *
from djeval import *
import csv, code, os
import cPickle as pickle
from sklearn.externals import joblib

NUM_GAMES=50000

DO_GB = bool(int(os.environ['DO_GB']))
DO_GOLEM = bool(int(os.environ['DO_GOLEM']))
DO_ERRORCHUNK = bool(int(os.environ['DO_ERRORCHUNK']))
CHAIN_VALIDATE = bool(int(os.environ['CHAIN_VALIDATE']))


def shell():
    vars = globals()
    vars.update(locals())
    shell = code.InteractiveConsole(vars)
    shell.interact()

msg("Hi! Reading eheaders")
eheaders_filename = '/data/eheaders.p'
eheaders_file = open(eheaders_filename, 'r')
eheaders = pickle.load(eheaders_file)
elos = eheaders['elos']
result = eheaders['result']
checkmate = eheaders['checkmate']
openings = eheaders['openings']
ocount = eheaders['opening_count']

msg("Hi! Reading crunched movescores from %s" % sys.argv[1])
crunched_path = sys.argv[1]
crunched_df = read_csv(crunched_path, sep=',', engine='c', index_col=['gamenum', 'side'])

if DO_GB:
    msg("Hi! Reading GB scores from %s" % sys.argv[2])
    gb_path = sys.argv[2]
    gb_df = read_csv(gb_path, sep=',', engine='c', index_col=['gamenum'])

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
# we have the gamelength column in another df, drop it here to avoid conflicts
depthstats_df.drop('gamelength', axis=1, inplace=True)

do_material = True
if do_material:
    msg("Hi! Reading material")
    material_path = '/data/material.csv'
    columns = [
    'gamenum',
    'material_break_0',
    'material_break_1',
    'material_break_2',
    'material_break_3',
    'material_break_4',
    'opening_length',
    'midgame_length',
    'endgame_length',
    'mean_acwsa',
    'mean_acwsa_0',
    'mean_acwsa_1',
    'mean_acwsa_2',
    'mean_acwsa_3',
    'mean_acwsa_4',
    'mean_acwsa_5',
    'mean_acwsa_6',
    'mean_acwsa_7',
    'mean_acwsa_8',
    'mean_acwsa_9',
    ]
    material_df = read_csv(material_path, sep=' ', engine='c', header=None, names=columns, index_col=False)
    material_df = material_df.set_index(['gamenum'])
    material_df = material_df.reindex(range(1, NUM_GAMES+1))
    material_df = material_df.fillna(material_df.mean())

msg("Reading ELOscored data")
eloscored_cols = [
    'gamenum',
    'final_elo',
    'final_ply',
    'final_num_games',
    'final_elo_stdev',
    'elopath_min',
    'elopath_max',
]
eloscored_df = read_csv('/data/data.pgn.eloscored21', sep=',', engine='c', header=None, names=eloscored_cols, index_col=False)
eloscored_df = eloscored_df.set_index(['gamenum'])

msg("Reading ELOscored data 4")
eloscored4_cols = [
    'gamenum',
    'final_elo',
    'final_ply',
    'final_num_games',
    'final_elo_stdev',
]
eloscored4_cols[1:] = [x + '_elo4' for x in eloscored4_cols[1:]]
eloscored4_df = read_csv('/data/data.pgn.eloscored4', sep=',', engine='c', header=None, names=eloscored4_cols, index_col=False)
eloscored4_df = eloscored4_df.set_index(['gamenum'])

msg("Reading ELOscored data 10")
eloscored10_cols = [
    'gamenum',
    'final_elo',
    'final_ply',
    'final_num_games',
    'final_elo_stdev',
]
eloscored10_cols[1:] = [x + '_elo10' for x in eloscored10_cols[1:]]
eloscored10_df = read_csv('/data/data.pgn.eloscored10', sep=',', engine='c', header=None, names=eloscored10_cols, index_col=False)
eloscored10_df = eloscored10_df.set_index(['gamenum'])

do_movemodel=True
if do_movemodel:
    msg("Hi! Reading moveaggs")
    move_aggs = joblib.load('/data/move_aggs.p')
    move_aggs.fillna(move_aggs.mean(), inplace=True)
    move_aggs = move_aggs[['mean', 'median', '25', '10', 'min', 'max', 'stdev']]
    msg("Hi! Reading wmoveaggs")
    wmove_aggs = joblib.load('/data/wmove_aggs.p')
    wmove_aggs.fillna(wmove_aggs.mean(), inplace=True)
    wmove_aggs.rename(columns={'elo_pred': 'moveelo_weighted'}, inplace=True)
    wmove_aggs = wmove_aggs['moveelo_weighted']

if DO_ERRORCHUNK:
    ch_agg_df = joblib.load('/data/chunk_aggs.p')
    ch_agg_df.index = ch_agg_df.index.droplevel('elo')
    ch_agg_df.columns = ['elochunk_' + x for x in ch_agg_df.columns]
    elorange_cols = list(ch_agg_df.columns.values)
    msg("elorange cols are %s" % elorange_cols)


msg("Hi! Setting up playergame rows")

msg('Preparing ELO df')
elo_rows = [[x[0][0], x[0][1], x[1]] for x in elos.items()]
elo_df = DataFrame(elo_rows, columns=['gamenum','side','elo'])
elo_df.set_index(['gamenum','side'], inplace=True)

msg('Joining DFs')
supplemental_dfs = [depthstats_df, elo_df, crunched_df]
if do_movemodel:
    supplemental_dfs.extend([move_aggs, wmove_aggs])
if DO_ERRORCHUNK:
    supplemental_dfs.append(ch_agg_df)
mega_df = concat(supplemental_dfs, axis=1)
if do_material:
    mega_df = mega_df.join(material_df, how='outer')
mega_df = mega_df.join(eloscored_df, how='outer')
mega_df = mega_df.join(eloscored4_df, how='outer')
mega_df = mega_df.join(eloscored10_df, how='outer')
if DO_GB:
    mega_df = mega_df.join(gb_df, how='outer')

yy_df = mega_df
msg("hi, columns are %s" % yy_df.columns)

# TODO confirm that all columns are there


def opening_feature(opening):
  if ocount[opening] < 20:
    return 'rare'
  if ocount[opening] < 200:
    return 'uncommon'
  return opening

msg("Hi! Computing additional features")
yy_df['opening_feature'] = [opening_feature(openings[x]) for x in yy_df.index.get_level_values('gamenum')]
yy_df['opening_count'] = [ocount[openings[x]] for x in yy_df.index.get_level_values('gamenum')]
yy_df['any_grit'] = (yy_df['grit'] > 0)
yy_df['major_grit'] = (yy_df['grit'] > 5)
yy_df['nmerror'] = log((-1 * yy_df['meanerror']).clip(1,60)).clip(1,4) - 2.53
yy_df['premature_quit'] = (yy_df['gameoutcome'] == -1) & (yy_df['my_final_equity'] > -100)
yy_df['drawn_game'] = (yy_df['gameoutcome'] == 0)
yy_df['ended_by_checkmate'] = yy_df['won_by_checkmate'] | yy_df['lost_by_checkmate']
yy_df['noblunders'] = (yy_df['blunderrate'] == 0)
yy_df['final_equity'] = yy_df['my_final_equity'].abs().clip(0,300)
yy_df['early_lead'] = yy_df['early_lead'].clip(0,100)
yy_df['mean_depth_clipped'] = yy_df['mean_depth'].clip(0,25)
yy_df['gamelength_clipped'] = yy_df['gamelength'].clip(20,200)


# prepare opponent_df with selected info about opponent
opponent_columns = ['meanerror', 'blunderrate', 'perfectrate', 'grit', 'meanecho', 'mate_created', 'mate_destroyed', 'q_error_one', 'q_error_two', 'stdeverror', 'elo', 'any_grit', 'noblunders', 'nmerror', 'mean_depths_agreeing_ratio', 'mean_deepest_agree_ratio', 'pct_sanemoves']
if DO_ERRORCHUNK:
    opponent_columns.extend(elorange_cols)
opponent_df = yy_df[opponent_columns]
opponent_df = opponent_df.reset_index()
opponent_df['side'] = opponent_df['side'] * -1
opponent_df.set_index(['gamenum', 'side'], inplace=True)
opponent_df.columns = ['opponent_' + x for x in opponent_df.columns]
yy_df = concat([yy_df, opponent_df], axis=1)

# more derived columns that use opponent comparisons
yy_df['elo_advantage'] = (yy_df['elo'] - yy_df['opponent_elo']).clip(-500, 500)
yy_df['max_nmerror'] = yy_df[['nmerror', 'opponent_nmerror']].max(axis=1)
yy_df['min_nmerror'] = yy_df[['nmerror', 'opponent_nmerror']].min(axis=1)
yy_df['max_meanecho'] = yy_df[['meanecho', 'opponent_meanecho']].max(axis=1)
yy_df['elo_avg'] = (yy_df['elo'] + yy_df['opponent_elo'])/2.0
yy_df['elo_advantage'] = (yy_df['elo'] - yy_df['opponent_elo'])
yy_df['winner_elo_advantage'] = yy_df['elo_advantage'] * yy_df['gameoutcome']


msg("Hi! Computing dummy variables")
categorical_features = ['opening_feature']
dummies = get_dummies(yy_df[categorical_features]).astype(np.int8)
yy_df = yy_df.join(dummies)

# fill in missing values
msg("Hi! Filling in missing values")
full_index = pandas.MultiIndex.from_product([range(1,NUM_GAMES + 1), [1,-1]], names=['gamenum', 'side'])
yy_df = yy_df.reindex(full_index)
yy_elo = yy_df['elo'].copy(True)
yy_df.fillna(yy_df.mean(numeric_only=True), inplace=True)
yy_df.fillna(False, inplace=True)
yy_df['elo'] = yy_elo

# stupid patch for some stupid opening feature that got assigned to False by fillna ?!!?!?!?
yy_df.loc[yy_df['opening_feature'] == False,'opening_feature'] = 'rare'

msg("Hi! Writing yy_df to disk")
yy_df.to_pickle(sys.argv[3])

msg("Column counts are:")
counts = yy_df.count(axis=0)
print counts

