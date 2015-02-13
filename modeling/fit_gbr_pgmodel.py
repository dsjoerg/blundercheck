#!/usr/bin/env python

import sys, time
import numpy as np
import cPickle as pickle
from pandas import DataFrame
from pandas import read_pickle
from pandas import get_dummies
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.cross_validation import cross_val_score
from sklearn.externals import joblib
from djeval import *

msg("Hi, reading yy_df.")
yy_df = read_pickle(sys.argv[1])

msg("Getting subset ready.")

train = yy_df[yy_df.meanerror.notnull() & yy_df.elo.notnull()]

features = list(yy_df.columns.values)
excluded_features = ['elo', 'opponent_elo', 'elo_advantage', 'elo_avg', 'winner_elo_advantage', 'opening_feature', 'ols_error']
for f in excluded_features:
    features.remove(f)

X = train[features].values
y = train['elo']

gbr = GradientBoostingRegressor(loss='lad', n_estimators=400, min_samples_leaf=10, min_samples_split=50)

msg("CROSS VALIDATING")
cvs = cross_val_score(gbr, X, y, cv=3, n_jobs=-1, scoring='mean_absolute_error')
print cvs
sys.stdout.flush()

msg("Fitting!")
gbr.fit(X, y)

msg("Saving model")
joblib.dump([gbr, features], sys.argv[2])

msg("Making predictions for all playergames")
yy_df['gbr_prediction'] = gbr.predict(yy_df[features].values)
yy_df['gbr_error'] = (yy_df['gbr_prediction'] - yy_df['elo']).abs()
yy_df['training'] = yy_df['elo'].notnull()
insample_scores = yy_df.groupby('training')['gbr_error'].agg({'mean' : np.mean, 'median' : np.median, 'stdev': np.std})
print insample_scores

msg("Writing yy_df back out with gbr predictions inside")
yy_df.to_pickle(sys.argv[1])

msg("Preparing Kaggle submission")
# map from eventnum to whiteelo,blackelo array

predictions = {}
for eventnum in np.arange(25001,50001):
  predictions[eventnum] = [0,0]

for row in yy_df[yy_df['elo'].isnull()][['gamenum', 'side', 'gbr_prediction']].values:
  eventnum = row[0]
  side = row[1]
  if side == 1:
    sideindex = 0
  else:
    sideindex = 1
  prediction = row[2]
  predictions[eventnum][sideindex] = prediction

submission = open('/data/submission.csv', 'w')
submission.write('Event,WhiteElo,BlackElo\n')
for eventnum in np.arange(25001,50001):
  submission.write('%i,%i,%i\n' % (eventnum, predictions[eventnum][0], predictions[eventnum][1]))
submission.close()
