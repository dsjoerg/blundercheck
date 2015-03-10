#!/usr/bin/env python

import csv, sys
import cPickle as pickle
from pandas import *

column_dtypes = {
    'halfply': np.float32,
    'moverscore': np.float32,
    'movergain': np.float32,
    'prevgain': np.float32,
    'move_piece': str,
    'move_dir': np.dtype('a2'),
    'move_dist': np.int8,
    'move_is_capture': bool,
    'move_is_check': bool,
    'bestmove_piece': str,
    'bestmove_dir': np.dtype('a2'),
    'bestmove_dist': np.int8,
    'bestmove_is_capture': bool,
    'bestmove_is_check': bool,
    'depth': np.float16,
    'seldepth': np.float16,
    'depths_agreeing': np.float16,
    'deepest_agree': np.float16,
    'num_bestmoves': np.float16,
    'num_bestmove_changes': np.float16,
    'bestmove_depths_agreeing': np.float16,
    'deepest_change': np.float16,
    'elo': np.float16,
    'side': np.int8,
    'gamenum': np.float32,
    'timecontrols': object,
    'white_material': np.float16,
    'black_material': np.float16,
    'game_phase': np.float16,
    'gb': np.float32,
    'gb12': np.float32,
}

columns = ['halfply','moverscore','movergain','prevgain','move_piece','move_dir','move_dist','move_is_capture','move_is_check','bestmove_piece','bestmove_dir','bestmove_dist','bestmove_is_capture','bestmove_is_check','depth','seldepth','depths_agreeing','deepest_agree','num_bestmoves','num_bestmove_changes','bestmove_depths_agreeing','deepest_change','elo','side','gamenum','white_material','black_material','game_phase','gb','gb12']

moves_df = read_csv(sys.stdin, engine='c', header=None, names=columns, dtype=column_dtypes, index_col=False)

print 'SHAPE', moves_df.shape
print moves_df.memory_usage(index=True).sum()
print moves_df.memory_usage(index=True)

# for the purposes of modeling we dont care about east-west differences
for colname in ['move_dir', 'bestmove_dir']:
    moves_df[colname].replace('NE', 'NW', inplace=True)
    moves_df[colname].replace('SE', 'SW', inplace=True)
    moves_df[colname].replace('E', 'W', inplace=True)

moves_df['sd_ratio'] = moves_df['seldepth'] / moves_df['depth']
moves_df['deepest_ar'] = moves_df['deepest_agree'] / moves_df['depth']
moves_df['depths_ar'] = moves_df['depths_agreeing'] / moves_df['depth']
moves_df['clippedgain'] = moves_df['movergain'].clip(-300,0)

categorical_features = [
    'move_dir',
    'bestmove_dir',
    'move_piece',
    'bestmove_piece',
    'timecontrols'
]

print 'SHAPE', moves_df.shape
print moves_df.memory_usage(index=True).sum()
print moves_df.memory_usage(index=True)

dummy_features = []
for index, cf in enumerate(categorical_features):
  dummies = get_dummies(moves_df[cf], prefix=cf).astype(np.int8)
  dummy_features.extend(dummies.columns.values)
  moves_df = moves_df.join(dummies)

moves_df.to_pickle(sys.argv[1])

moves_info = {'categorical_features':categorical_features}
moves_file = open(sys.argv[1] + '.info', 'w')
pickle.dump(moves_info, moves_file)
moves_file.close()
