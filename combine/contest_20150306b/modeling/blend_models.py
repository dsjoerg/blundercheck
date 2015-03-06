#!/usr/bin/env python

import sys
import numpy as np

from pandas import *
from sklearn.metrics import mean_absolute_error
from djeval import *

n_estimators = 200
n_jobs = -1

msg("Hi, reading yy_df.")
yy_df = read_pickle(sys.argv[1])

msg("Getting subset ready.")
train = yy_df[yy_df.elo.notnull()]
train = yy_df[yy_df['gamenum'] < 25000]

for blend in np.arange(0, 1.01, 0.1):
    blended_prediction = (blend * train['ols_prediction']) + ((1.0 - blend) * train['rfr_prediction'])
    blended_score = mean_absolute_error(blended_prediction, train['elo'])
    print blend, blended_score
