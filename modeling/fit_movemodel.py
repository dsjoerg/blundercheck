#!/usr/bin/env python

import sys, time
import numpy as np
import pygraphviz as pgv
from StringIO import StringIO
from pandas import read_pickle
from pandas import DataFrame
from sklearn.externals import joblib
from sklearn.cross_validation import cross_val_score
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from sklearn import tree

NUM_TO_USE = 2000
n_estimators = 200
cv_groups = 3

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

train = moves_df[moves_df['elo'].notnull()]
#X = train[0:NUM_TO_USE][features_to_use].values
X = train[0:NUM_TO_USE][features_to_use]
y = train[0:NUM_TO_USE]['elo']

if False:
    some_filename = "foobaby"
    joblib.dump(X, some_filename)
    X = joblib.load(some_filename, mmap_mode='r+')

rfr = RandomForestRegressor(n_estimators=n_estimators, n_jobs=-1, min_samples_leaf=100, min_samples_split=500, verbose=1)

begin_time = time.time()
cvs = cross_val_score(rfr, X, y, cv=cv_groups, n_jobs=1, scoring='mean_absolute_error')
print "Crosss validation took %f seconds with %i records, %i estimators and %i CV groups" % ((time.time() - begin_time), len(X), n_estimators, cv_groups)
print "Results: %s" % str(cvs)

print "Fitting model"
begin_time = time.time()
rfr.fit(X, y)
print "Model fit took %f seconds." % (time.time() - begin_time)

print "Feature importances:"
print DataFrame([rfr.feature_importances_, features_to_use]).transpose().sort([0], ascending=False)

joblib.dump(rfr, sys.argv[2])

dot_data = StringIO()
tree.export_graphviz(rfr.estimators_[0], out_file=dot_data, feature_names=features_to_use)
print dot_data.getvalue()

B=pgv.AGraph(dot_data.getvalue())
B.layout('dot')
B.draw('/data/rfr.png') # draw png

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

    DataFrame([rfr.feature_importances_, features_to_use])

    train['rfr_error'] = (train['rfr_prediction'] - train['elo']).abs()
    train[train['rfr_error'] > 600][['gamenum', 'side', 'halfply', 'rfr_prediction', 'elo']].head(20)

    moves_dfd[['gamenum','halfply','rfr_prediction']]

    move_aggs_file = open('/home/beaker/notebooks/kaggle_data/move_aggs_20150205b.p', 'wb')
    pickle.dump(move_aggs, move_aggs_file)
    move_aggs_file.close()
