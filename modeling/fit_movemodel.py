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
PREDICT_N = 100000
n_estimators = 200
cv_groups = 3
n_jobs = -1

# For when we were messing around with blundergroups:
#
# so that we can test the idea that dataset size being equal,
# we make better predictions with data specifically in that blundergroup
#
# CROSS_VALIDATION_N = 7500

# debugging 'Cannot allocate memory'
n_jobs = 1


if False:
    inflation = 4
    CROSS_VALIDATION_N = inflation * CROSS_VALIDATION_N
    MIN_SAMPLES_LEAF = inflation * MIN_SAMPLES_LEAF
    MIN_SAMPLES_SPLIT = inflation * MIN_SAMPLES_SPLIT
    FITTING_N = inflation * FITTING_N

just_testing = False
if just_testing:
    CROSS_VALIDATION_N = 1500
    n_estimators = 2
    n_jobs = -1

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
#    rfr_here = RandomForestRegressor(n_estimators=n_estimators, n_jobs=n_jobs, min_samples_leaf=msl, min_samples_split=mss, verbose=1)
    rfr_here = RandomForestRegressor(n_estimators=n_estimators, n_jobs=n_jobs, min_samples_leaf=MIN_SAMPLES_LEAF, min_samples_split=MIN_SAMPLES_SPLIT, verbose=1)
    crossval_X = sampled_df[features_to_use]
    crossval_y = sampled_df['elo']
    crossval_weights = sampled_df['weight']

    msg("Starting cross validation. %i records" % sample_size)
    begin_time = time.time()
    cvs = cross_val_score(rfr_here, crossval_X, crossval_y, cv=cv_groups, n_jobs=n_jobs, scoring='mean_absolute_error', fit_params={'sample_weight': crossval_weights})
    msg("Cross validation took %f seconds with %i threads, %i records, %i estimators and %i CV groups" % ((time.time() - begin_time), n_jobs, len(crossval_X), n_estimators, cv_groups))
    msg("Results: %f, %s" % (np.mean(cvs), str(cvs)))
    return np.mean(cvs)


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

features_to_use = [col for col in moves_df.columns if (col not in features_to_exclude and col not in categorical_features)]
#features_to_use = ['moverscore', 'halfply', 'movergain', 'side']

insample_df = moves_df[moves_df['elo'].notnull()]

do_blunder_groups = False
if do_blunder_groups:
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

rfr = RandomForestRegressor(n_estimators=n_estimators, n_jobs=n_jobs, min_samples_leaf=MIN_SAMPLES_LEAF, min_samples_split=MIN_SAMPLES_SPLIT, verbose=1)

do_crossval = False
if do_crossval:
    crossval_df = sample_df(insample_df, CROSS_VALIDATION_N)
    crossval_X = crossval_df[features_to_use]
    crossval_y = crossval_df['elo']
    crossval_weights = crossval_df['weight']
    movergain_index = features_to_use.index('movergain')

    msg("Starting full DF cross validation")
    begin_time = time.time()
    # using n_jobs=1 here because the parallelization of cross_val_score interferes with
    # our gross hack of stashing info about blundergroups into a global variable as a side effect

    if do_blunder_groups:
        cvs = cross_val_score(rfr, crossval_X, crossval_y, cv=cv_groups, n_jobs=1, scoring=group_scorer, fit_params={'sample_weight': crossval_weights})
    else:
        cvs = cross_val_score(rfr, crossval_X, crossval_y, cv=cv_groups, n_jobs=n_jobs, scoring='mean_absolute_error')
    msg("Cross validation took %f seconds with %i threads, %i records, %i estimators and %i CV groups" % ((time.time() - begin_time), n_jobs, len(crossval_X), n_estimators, cv_groups))
    msg("Results: %f, %s" % (np.mean(cvs), str(cvs)))

if do_blunder_groups:
    msg("per-blundergroup results:")
    #for bcv in blunder_cv_results:
    #    msg("here: %s" % bcv)
    concat_df = concat(blunder_cv_results, axis=1)
    concat_df['LAD from RFR on whole dataset'] = concat_df.mean(axis=1)
    msg("full dataframe cross-validation, per blundergroup:\n%s" % concat_df)

    concat_df = concat([concat_df.mean(axis=1), cv_scores, lads], axis=1)
    concat_df.columns = ['single RFR', 'RFR per blundergroup', 'mean-value benchmark']
    msg("everything together:\n%s" % concat_df)


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
