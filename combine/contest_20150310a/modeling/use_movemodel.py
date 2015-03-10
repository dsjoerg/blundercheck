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

PREDICT_N = 100000

msg("Hi, reading moves.")
moves_df = read_pickle(sys.argv[1])

thing = joblib.load(sys.argv[2])
rfr = thing[0]
features_to_use = thing[1]

all_y_preds = []
all_y_stds = []

msg("Computing predictions in chunks")
begin_time = time.time()

for i in range(0, len(moves_df) + PREDICT_N, PREDICT_N):
    predict_df = moves_df.iloc[i : i + PREDICT_N]
    predict_features = predict_df[features_to_use]
    y_pred, y_std = rfr.predict(predict_features, with_std=True)
    all_y_preds.append(y_pred)
    all_y_stds.append(y_std)

msg("Predicting took %f seconds." % ((time.time() - begin_time)))

msg("i got %i all_y_preds which concatenate to %i, shape %s.  moves_df is %i." % (len(all_y_preds), len(np.concatenate(all_y_preds)), str(np.concatenate(all_y_preds).shape), len(moves_df)))

msg("Putting predictions back into moves_df")
moves_df['elo_predicted'] = np.concatenate(all_y_preds)
moves_df['elo_pred_std'] = np.concatenate(all_y_stds)
moves_df['elo_pred_std'].fillna(40, inplace=True)
moves_df['elo_pred_weight'] = 1. / (moves_df['elo_pred_std'] * moves_df['elo_pred_std'])
moves_df['elo_weighted_pred'] = moves_df['elo_pred_weight'] * moves_df['elo_predicted']

msg("Writing moves_df back out with rfr predictions inside")
moves_df.to_pickle(sys.argv[1])
msg("Done.")

show_bestworst = False
if show_bestworst:
    msg("Highest and lowest std from in-sample portion:")
    predict_insample_df = moves_df[moves_df['elo'].notnull()]
    summary_df = predict_insample_df[['elo_predicted', 'elo_pred_std', 'gamenum', 'halfply', 'elo', 'elo_pred_weight', 'elo_weighted_pred']]
    for asc in [True, False]:
        print summary_df.sort(['elo_pred_std'], ascending=asc).head(10)
