#!/usr/bin/env python

import numpy as np
from pandas import read_pickle
from sklearn.externals import joblib
from sklearn.cross_validation import cross_val_score
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error


NUM_TO_USE = 2000

moves_df = read_pickle(sys.argv[1])

features_to_exclude = [
'elo',
]
features_to_use = [col for col in moves_df.columns if col not in features_to_exclude]

train = moves_df[moves_df['elo'].notnull()]
X = train[0:NUM_TO_USE][features_to_use].values
y = train[0:NUM_TO_USE]['elo']

if False:
    some_filename = "foobaby"
    joblib.dump(X, some_filename)
    X = joblib.load(some_filename, mmap_mode='r+')

rfr = RandomForestRegressor(n_estimators=100, n_jobs=-1, min_samples_leaf=100, min_samples_split=500, verbose=1)
cvs = cross_val_score(rfr, X, y, cv=3, n_jobs=-1, scoring='mean_absolute_error')
print cvs

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
                                       }

    DataFrame([rfr.feature_importances_, features_to_use]

    train['rfr_error'] = (train['rfr_prediction'] - train['elo']).abs()
    train[train['rfr_error'] > 600][['gamenum', 'side', 'halfply', 'rfr_prediction', 'elo']].head(20)

    moves_dfd[['gamenum','halfply','rfr_prediction']

    move_aggs_file = open('/home/beaker/notebooks/kaggle_data/move_aggs_20150205b.p', 'wb')
    pickle.dump(move_aggs, move_aggs_file)
    move_aggs_file.close()
