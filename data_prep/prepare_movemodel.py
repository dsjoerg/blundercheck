#!/usr/bin/env python

import csv, sys
import cPickle as pickle
from pandas import *

columns = [
    'halfply',
    'moverscore',
    'movergain',
    'prevgain',
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
    'timecontrols',
    'white_material',
    'black_material',
    'game_phase',
]


moves_df = read_csv(sys.stdin, engine='c', header=None, names=columns, index_col=False)

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

dummy_features = []
for index, cf in enumerate(categorical_features):
  dummies = get_dummies(moves_df[cf], prefix=cf)
  dummy_features.extend(dummies.columns.values)
  moves_df = moves_df.join(dummies, copy=False)

moves_df.to_pickle(sys.argv[1])

moves_info = {'categorical_features':categorical_features}
moves_file = open(sys.argv[1] + '.info', 'w')
pickle.dump(moves_info, moves_file)
moves_file.close()
