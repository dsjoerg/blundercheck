#!/usr/bin/env python

import sys, time
import numpy as np
from StringIO import StringIO
import cPickle as pickle
from pandas import DataFrame
from pandas import concat
from pandas import read_pickle
from sklearn.externals import joblib
from sklearn.cross_validation import cross_val_score
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from djeval import *

CROSS_VALIDATION_N = 150000
FITTING_N = 50000
PREDICT_N = 400000
n_estimators = 200
cv_groups = 3
n_jobs = -1

just_testing = False
if just_testing:
    CROSS_VALIDATION_N = 100
    FITTING_N = 100
    PREDICT_N = 400000
    n_estimators = 5

def sample_df(df, n_to_sample):
    row_indexes = np.random.choice(df.index.values, n_to_sample, replace=False)
    return df.ix[row_indexes]

msg("Hi, reading moves.")
moves_df = read_pickle(sys.argv[1])

moves_file = open(sys.argv[1] + '.info', 'rb')
moves_info = pickle.load(moves_file)
categorical_features = moves_info['categorical_features']

msg("Computing weights")
game_weights = (1. / (moves_df.groupby('gamenum')['halfply'].agg({'max':np.max}).clip(1,1000)))['max']
moves_df['weight'] = moves_df['gamenum'].map(game_weights)
msg("Done")

moves_df['abs_moverscore'] = moves_df['moverscore'].abs()

features_to_exclude = [
'elo',
'gamenum',
'weight',
'clippedgain',
'moverscore'
]

msg("canonicalizing directions")
for colname in ['move_dir', 'bestmove_dir']:
    moves_df[colname].replace('NE', 'NW', inplace=True)
    moves_df[colname].replace('SE', 'SW', inplace=True)
    moves_df[colname].replace('E', 'W', inplace=True)
msg("done")

features_to_use = [col for col in moves_df.columns if (col not in features_to_exclude and col not in categorical_features)]

insample_df = moves_df[moves_df['elo'].notnull()]
crossval_df = sample_df(insample_df, CROSS_VALIDATION_N)
crossval_X = crossval_df[features_to_use]
crossval_y = crossval_df['elo']
crossval_weights = crossval_df['weight']

rfr = RandomForestRegressor(n_estimators=n_estimators, n_jobs=n_jobs, min_samples_leaf=300, min_samples_split=1000, verbose=1)

msg("Starting cross validation")
begin_time = time.time()
cvs = cross_val_score(rfr, crossval_X, crossval_y, cv=cv_groups, n_jobs=n_jobs, scoring='mean_absolute_error', fit_params={'sample_weight': crossval_weights})
#cvs = cross_val_score(rfr, crossval_X, crossval_y, cv=cv_groups, n_jobs=n_jobs, scoring='mean_absolute_error')
msg("Cross validation took %f seconds with %i threads, %i records, %i estimators and %i CV groups" % ((time.time() - begin_time), n_jobs, len(crossval_X), n_estimators, cv_groups))
msg("Results: %f, %s" % (np.mean(cvs), str(cvs)))

fitting_df = sample_df(insample_df, FITTING_N)
fitting_X = fitting_df[features_to_use]
fitting_y = fitting_df['elo']
fitting_weights = fitting_df['weight'].values

msg("Fitting model")
begin_time = time.time()
rfr.fit(fitting_X, fitting_y, sample_weight=fitting_weights)
#rfr.fit(fitting_X, fitting_y)
msg("Model fit took %f seconds on %i records." % ((time.time() - begin_time), len(fitting_X)))

msg("Saving model")
joblib.dump([rfr, features_to_use], sys.argv[2])


all_y_preds = []
all_y_stds = []

msg("Computing predictions in chunks")
begin_time = time.time()

for i in range(0, len(moves_df) + PREDICT_N, PREDICT_N):
    predict_df = moves_df.iloc[i : i + PREDICT_N]
    predict_features = predict_df[features_to_use]

#    msg("Predicting for chunk %i" % i)
#    print("Chunk head:")
#    print predict_df.head()
    y_pred, y_std = rfr.predict(predict_features, with_std=True)
    #y_pred = rfr.predict(X)
    
    all_y_preds.append(y_pred)
    all_y_stds.append(y_std)
#    print "Got %s, and %s" % (type(y_pred), y_pred.shape)

msg("Predicting took %f seconds." % ((time.time() - begin_time)))

msg("i got %i all_y_preds which concatenate to %i, shape %s.  moves_df is %i." % (len(all_y_preds), len(np.concatenate(all_y_preds)), str(np.concatenate(all_y_preds).shape), len(moves_df)))

msg("Putting predictions back into moves_df")
moves_df['elo_predicted'] = np.concatenate(all_y_preds)
moves_df['elo_pred_std'] = np.concatenate(all_y_stds)

msg("Highest and lowest std from in-sample portion:")
predict_insample_df = moves_df[moves_df['elo'].notnull()]
summary_df = predict_insample_df[['elo_predicted', 'elo_pred_std', 'gamenum', 'halfply', 'elo']]
for asc in [True, False]:
    print summary_df.sort(['elo_pred_std'], ascending=asc).head(10)
msg("Done.")


exd = moves_df[['gamenum','side','elo_predicted']]
grp = exd.groupby(['gamenum', 'side'])
move_aggs = grp['elo_predicted'].agg({'mean': np.mean, 'median' : np.median, 'stdev': np.std,
                                      '25': lambda x: np.percentile(x, 25),
                                      '10': lambda x: np.percentile(x, 10),
                                      'min': lambda x: np.min(x),
                                      'max': lambda x: np.max(x),
                                  })


joblib.dump(move_aggs, '/data/move_aggs.p')
