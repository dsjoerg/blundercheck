#!/usr/bin/env python

import sys, time
import numpy as np
from StringIO import StringIO
import cPickle as pickle
from pandas import DataFrame
from pandas import concat
from pandas import read_pickle
from pandas import cut
from pandas import concat
from pandas import set_option
from sklearn.externals import joblib
from sklearn.cross_validation import cross_val_score
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from djeval import *

msg("Hi, reading moves.")
moves_df = read_pickle(sys.argv[1])


print 'SHAPE', moves_df.shape
set_option('display.max_rows', None)
print moves_df.memory_usage(index=True).sum()
print moves_df.memory_usage(index=True)

grp = moves_df.groupby(['gamenum', 'side'])
move_aggs = grp['elo_predicted'].agg({'mean': np.mean, 'median' : np.median, 'stdev': np.std,
                                      '25': lambda x: np.percentile(x, 25),
                                      '10': lambda x: np.percentile(x, 10),
                                      'min': lambda x: np.min(x),
                                      'max': lambda x: np.max(x),
                                  })


joblib.dump(move_aggs, '/data/move_aggs.p')

exd = moves_df[['gamenum','side','elo_weighted_pred','elo_pred_weight']]
grp = exd.groupby(['gamenum', 'side'])
wmove_aggs = grp.aggregate(np.sum)
wmove_aggs['elo_pred'] = wmove_aggs['elo_weighted_pred'] / wmove_aggs['elo_pred_weight']
joblib.dump(wmove_aggs, '/data/wmove_aggs.p')
print wmove_aggs.head()
