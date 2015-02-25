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
from sklearn.externals import joblib
from sklearn.cross_validation import cross_val_score
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from djeval import *

msg("Hi, reading moves.")
moves_df = read_pickle(sys.argv[1])

train_df = moves_df[moves_df['elo'].notnull()]
the_iter = train_df.iterrows()
for ix, row in the_iter:
    print '%f | halfply:%f moverscore:%f side:%i depth:%f seldepth:%f num_bestmoves:%f num_bestmove_changes:%f bestmove_depths_agreeing:%f deepest_change:%f elo:%f' % (row['movergain'], row['halfply'], row['moverscore'], row['side'], row['depth'], row['seldepth'], row['num_bestmoves'], row['num_bestmove_changes'], row['bestmove_depths_agreeing'], row['deepest_change'], row['elo'])
#    print '%f | garbage:%f' % (row['movergain'], np.random.rand())
