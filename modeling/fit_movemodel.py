#!/usr/bin/env python

import sys, time
import numpy as np
from StringIO import StringIO
from pandas import read_pickle
from pandas import DataFrame
from sklearn.externals import joblib
from sklearn.cross_validation import cross_val_score
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

CROSS_VALIDATION_N = 20000
FITTING_N = 100000
n_estimators = 1
cv_groups = 3

def sample_df(df, n_to_sample):
    row_indexes = np.random.choice(df.index.values, n_to_sample, replace=False)
    return df.ix[row_indexes]

moves_df = read_pickle(sys.argv[1])

features_to_exclude = [
'elo',
'gamenum'
]
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

features_to_use = [col for col in moves_df.columns if (col not in features_to_exclude and col not in categorical_features)]
#print "Using features %s" % str(features_to_use)

training_df = moves_df[moves_df['elo'].notnull()]

crossval_df = sample_df(training_df, CROSS_VALIDATION_N)
crossval_X = crossval_df[features_to_use]
crossval_y = crossval_df['elo']

rfr = RandomForestRegressor(n_estimators=n_estimators, n_jobs=-1, min_samples_leaf=300, min_samples_split=1000, verbose=1)

begin_time = time.time()
cvs = cross_val_score(rfr, crossval_X, crossval_y, cv=cv_groups, n_jobs=-1, scoring='mean_absolute_error')
print "Crosss validation took %f seconds with %i records, %i estimators and %i CV groups" % ((time.time() - begin_time), len(crossval_X), n_estimators, cv_groups)
print "Results: %s" % str(cvs)

fitting_df = sample_df(train, FITTING_N)
fitting_X = crossval_df[features_to_use]
fitting_y = crossval_df['elo']

print "Fitting model"
begin_time = time.time()
rfr.fit(fitting_X, fitting_y)
print "Model fit took %f seconds." % (time.time() - begin_time)

joblib.dump([rfr, features_to_use], sys.argv[2])

print "Predicting..."
begin_time = time.time()
training_features = training_df[features_to_use]
y_pred, y_std = rfr.predict(training_features, with_std=True)
summary_df = DataFrame([y_pred, y_std, training_features['gamenum'], training_features['halfply'], training_features['elo']])
summary_df = summary_df.transpose()
summary_df.columns = ['y_pred', 'y_std', 'gamenum', 'halfply', 'elo']
for asc in [True, False]:
    print summary_df.sort(['y_std'], ascending=asc).head(10)
print "Predicting took %f seconds." % (time.time() - begin_time)

if False:
    rfr.fit(X, y)
    joblib.dump(rfr, rfr_path)
    X = moves_dfd[features_to_use].values
    moves_dfd['rfr_prediction'] = rfr.predict(X)
    exd = moves_dfd
    exd = moves_dfd[['gamenum','side','rfr_prediction']]
    grp = exd.groupby(['gamenum', 'side'])
    move_aggs = grp['rfr_prediction'].agg({'mean': np.mean, 'median' : np.median, 'stdev': np.std,
                                           '25': lambda x: np.percentile(x, 25),
                                           '10': lambda x: np.percentile(x, 10),
                                           'min': lambda x: np.min(x),
                                           'max': lambda x: np.max(x),
                                       })

    train['rfr_error'] = (train['rfr_prediction'] - train['elo']).abs()
    train[train['rfr_error'] > 600][['gamenum', 'side', 'halfply', 'rfr_prediction', 'elo']].head(20)

    moves_dfd[['gamenum','halfply','rfr_prediction']]

    move_aggs_file = open('/home/beaker/notebooks/kaggle_data/move_aggs_20150205b.p', 'wb')
    pickle.dump(move_aggs, move_aggs_file)
    move_aggs_file.close()
