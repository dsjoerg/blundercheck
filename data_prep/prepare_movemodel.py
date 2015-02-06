#!/usr/bin/env python

import csv, sys
from pandas import *

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
    'elo',
    'side',
    'gamenum',
]


moves_df = read_csv(sys.stdin, engine='c', header=None, names=columns, index_col=False)

moves_df['sd_ratio'] = moves_df['seldepth'] / moves_df['depth']
moves_df['deepest_ar'] = moves_df['deepest_agree'] / moves_df['depth']
moves_df['depths_ar'] = moves_df['depths_agreeing'] / moves_df['depth']
moves_df['clippedgain'] = moves_df['movergain'].clip(-300,0)

categorical_features = [
    'move_dir',
    'bestmove_dir',
    'move_piece',
    'bestmove_piece',
    'move_is_capture',
    'move_is_check',
    'bestmove_is_capture',
    'bestmove_is_check',
]

dummy_features = []
for index, cf in enumerate(categorical_features):
  dummies = get_dummies(moves_df[cf], prefix=cf)
  dummy_features.extend(dummies.columns.values)
  moves_df = moves_df.join(dummies)

moves_df.to_hdf(sys.argv[1], 'table')
