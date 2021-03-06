#!/usr/bin/env python

import sys, time
import numpy as np
import cPickle as pickle
from pandas import *
from sklearn.ensemble import RandomForestRegressor
from sklearn.cross_validation import cross_val_score
from sklearn.externals import joblib
from sklearn import tree
import pygraphviz as pgv
from StringIO import StringIO
from djeval import *

n_estimators = 200
n_jobs = -1

msg("Hi, reading yy_df.")
yy_df = read_pickle(sys.argv[1])

msg("Getting subset ready.")

train = yy_df[yy_df.meanerror.notnull() & yy_df.elo.notnull()]

features = list(yy_df.columns.values)
categorical_features = ['opening_feature', 'timecontrols']
excluded_features = ['elo', 'opponent_elo', 'elo_advantage', 'elo_avg', 'winner_elo_advantage', 'ols_error', 'gbr_prediction', 'gbr_error']
excluded_features.extend(categorical_features)
for f in excluded_features:
    features.remove(f)

X = train[features].values
y = train['elo']

rfr = RandomForestRegressor(n_estimators=n_estimators, n_jobs=n_jobs, min_samples_leaf=10, min_samples_split=50, verbose=1)

msg("CROSS VALIDATING")
cvs = cross_val_score(rfr, X, y, cv=3, n_jobs=-1, scoring='mean_absolute_error')
print cvs
sys.stdout.flush()

msg("Fitting!")
rfr.fit(X, y)

msg("Saving model")
joblib.dump([rfr, features], sys.argv[2])

msg("Making predictions for all playergames")
yy_df['rfr_prediction'] = rfr.predict(yy_df[features].values)
yy_df['rfr_error'] = (yy_df['rfr_prediction'] - yy_df['elo']).abs()
insample_scores = yy_df.groupby('training')['rfr_error'].agg({'mean' : np.mean, 'median' : np.median, 'stdev': np.std})
print insample_scores

msg("Error summary by ELO:")
elo_centuries = cut(yy_df['elo'], 20)
print yy_df.groupby(elo_centuries)['rfr_error'].agg({'sum': np.sum, 'count': len, 'mean': np.mean})

msg("Writing yy_df back out with predictions inside")
yy_df.to_pickle(sys.argv[1])

msg("Preparing Kaggle submission")
# map from eventnum to whiteelo,blackelo array

predictions = {}
for eventnum in np.arange(25001,50001):
  predictions[eventnum] = [0,0]

for row in yy_df[yy_df['elo'].isnull()][['gamenum', 'side', 'rfr_prediction']].values:
  eventnum = row[0]
  side = row[1]
  if side == 1:
    sideindex = 0
  else:
    sideindex = 1
  prediction = row[2]
  predictions[eventnum][sideindex] = prediction

submission = open('/data/submission_rfr.csv', 'w')
submission.write('Event,WhiteElo,BlackElo\n')
for eventnum in np.arange(25001,50001):
  submission.write('%i,%i,%i\n' % (eventnum, predictions[eventnum][0], predictions[eventnum][1]))
submission.close()

print "OOB score:"
print rfr.oob_score

print "Feature importances:"
print DataFrame([rfr.feature_importances_, features]).transpose().sort([0], ascending=False)

print "There are %i trees." % len(rfr.estimators_)

dot_data = StringIO()
tree.export_graphviz(rfr.estimators_[0].tree_, out_file=dot_data, feature_names=features)
print dot_data.getvalue()

B=pgv.AGraph(dot_data.getvalue())
B.layout('dot')
B.draw('/data/rfr.png') # draw png

print "Wrote first tree to /data/rfr.png"
