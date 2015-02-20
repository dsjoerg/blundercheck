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

CROSS_VALIDATION_N = 150000
MIN_SAMPLES_LEAF = 300
MIN_SAMPLES_SPLIT = 1000
FITTING_N = 50000
PREDICT_N = 400000
n_estimators = 200
cv_groups = 3
n_jobs = -1


if False:
    inflation = 4
    CROSS_VALIDATION_N = inflation * CROSS_VALIDATION_N
    MIN_SAMPLES_LEAF = inflation * MIN_SAMPLES_LEAF
    MIN_SAMPLES_SPLIT = inflation * MIN_SAMPLES_SPLIT
    FITTING_N = inflation * FITTING_N

just_testing = True
if just_testing:
    CROSS_VALIDATION_N = 1500
    n_estimators = 2
    n_jobs = 1

blunder_cv_results = []


def sample_df(df, n_to_sample):
    if n_to_sample >= len(df.index.values):
        return df

    row_indexes = np.random.choice(df.index.values, n_to_sample, replace=False)
    return df.ix[row_indexes]

def group_scorer(estimator, X, y):
    pred_y = estimator.predict(X)
    msg("GROUPED SCORES FOR a CV GROUP:")
    dfx = DataFrame(X, columns=features_to_use)
    dfx['pred_abserror'] = abs(pred_y - y)
    blunder_cvgroups, blunder_cvbins = cut(dfx['movergain'], blunder_cats, retbins=True)
    blunder_cvgrouped = dfx.groupby(blunder_cvgroups)['pred_abserror'].agg({'lad': np.mean})
    blunder_cv_results.append(blunder_cvgrouped)
    msg("scores: %s" % str(blunder_cvgrouped))
    return mean_absolute_error(y, pred_y)

def crossval_rfr(df):
    sampled_df = sample_df(df, CROSS_VALIDATION_N)
    sample_size = len(sampled_df)
    mss = max([sample_size / 150, 100])
    msl = max([sample_size / 450,  30])
    rfr_here = RandomForestRegressor(n_estimators=n_estimators, n_jobs=n_jobs, min_samples_leaf=msl, min_samples_split=mss, verbose=1)
    crossval_X = sampled_df[features_to_use]
    crossval_y = sampled_df['elo']
    crossval_weights = sampled_df['weight']

    msg("Starting cross validation. %i records" % sample_size)
    begin_time = time.time()
    cvs = cross_val_score(rfr_here, crossval_X, crossval_y, cv=cv_groups, n_jobs=n_jobs, scoring='mean_absolute_error', fit_params={'sample_weight': crossval_weights})
    msg("Cross validation took %f seconds with %i threads, %i records, %i estimators and %i CV groups" % ((time.time() - begin_time), n_jobs, len(crossval_X), n_estimators, cv_groups))
    msg("Results: %f, %s" % (np.mean(cvs), str(cvs)))
    return (cvs, np.mean(cvs))


msg("Hi, reading moves.")
moves_df = read_pickle(sys.argv[1])

moves_file = open(sys.argv[1] + '.info', 'rb')
moves_info = pickle.load(moves_file)
categorical_features = moves_info['categorical_features']

msg("Computing weights")
game_weights = (1. / (moves_df.groupby('gamenum')['halfply'].agg({'max':np.max}).clip(1,1000)))['max']
moves_df['weight'] = moves_df['gamenum'].map(game_weights)
msg("Done")

#moves_df['abs_moverscore'] = moves_df['moverscore'].abs()

features_to_exclude = [
'elo',
'weight',
'clippedgain',
]

msg("canonicalizing directions")
for colname in ['move_dir', 'bestmove_dir']:
    moves_df[colname].replace('NE', 'NW', inplace=True)
    moves_df[colname].replace('SE', 'SW', inplace=True)
    moves_df[colname].replace('E', 'W', inplace=True)
msg("done")

features_to_use = [col for col in moves_df.columns if (col not in features_to_exclude and col not in categorical_features)]
#features_to_use = ['moverscore', 'halfply', 'movergain', 'side']

insample_df = moves_df[moves_df['elo'].notnull()]

blunder_cats = [-1e9,-1024,-512,-256,-128,-64,-32, -16, -8, -1, 0]
blunder_groups, blunder_bins = cut(insample_df['movergain'], blunder_cats, retbins=True)

msg("Doing RFR CV per blunder group")
blunder_grouped = insample_df.groupby(blunder_groups)
cv_scores = blunder_grouped.apply(lambda x: crossval_rfr(x))
msg("SCORES:")
msg(cv_scores)

msg("blunder group errors vs mean-value")
lads = blunder_grouped.apply(lambda x: np.mean(abs(x['elo'] - np.mean(x['elo']))))
msg(lads)

crossval_df = sample_df(insample_df, CROSS_VALIDATION_N)
crossval_X = crossval_df[features_to_use]
crossval_y = crossval_df['elo']
crossval_weights = crossval_df['weight']
movergain_index = features_to_use.index('movergain')

rfr = RandomForestRegressor(n_estimators=n_estimators, n_jobs=n_jobs, min_samples_leaf=MIN_SAMPLES_LEAF, min_samples_split=MIN_SAMPLES_SPLIT, verbose=1)

msg("Starting full DF cross validation")
begin_time = time.time()
cvs = cross_val_score(rfr, crossval_X, crossval_y, cv=cv_groups, n_jobs=n_jobs, scoring=group_scorer, fit_params={'sample_weight': crossval_weights})
#cvs = cross_val_score(rfr, crossval_X, crossval_y, cv=cv_groups, n_jobs=n_jobs, scoring='mean_absolute_error')
msg("Cross validation took %f seconds with %i threads, %i records, %i estimators and %i CV groups" % ((time.time() - begin_time), n_jobs, len(crossval_X), n_estimators, cv_groups))
msg("Results: %f, %s" % (np.mean(cvs), str(cvs)))

msg("per-blundergroup results:")
#for bcv in blunder_cv_results:
#    msg("here: %s" % bcv)
concat_df = concat(blunder_cv_results, axis=1)
concat_df['avg_lad'] = concat_df.mean(axis=1)
msg("concat: %s" % concat_df)

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
moves_df['elo_pred_std'].fillna(40, inplace=True)
moves_df['elo_pred_weight'] = 1. / (moves_df['elo_pred_std'] * moves_df['elo_pred_std'])
moves_df['elo_weighted_pred'] = moves_df['elo_pred_weight'] * moves_df['elo_predicted']

msg("Highest and lowest std from in-sample portion:")
predict_insample_df = moves_df[moves_df['elo'].notnull()]
summary_df = predict_insample_df[['elo_predicted', 'elo_pred_std', 'gamenum', 'halfply', 'elo', 'elo_pred_weight', 'elo_weighted_pred']]
for asc in [True, False]:
    print summary_df.sort(['elo_pred_std'], ascending=asc).head(10)
msg("Done.")


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

msg("Writing moves_df back out with rfr predictions inside")
moves_df.to_pickle(sys.argv[1])
