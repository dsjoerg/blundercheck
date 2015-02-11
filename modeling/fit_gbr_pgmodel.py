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

# TODO save the dummies along with yy_df
dummies = get_dummies(yy_df['opening_feature'])

train = yy_df[yy_df.meanerror.notnull() & yy_df.elo.notnull()]

                    
features = ['nmerror',
            'blunderrate', 'noblunders', 
            'perfectrate',
            'gameoutcome',
            'won_by_checkmate', 'lost_by_checkmate', 'ended_by_checkmate',
            'my_final_equity', 'final_equity',
            'grit', 'any_grit', 'opponent_any_grit', 'major_grit',
            'mate_created', 'mate_destroyed', 'premature_quit',
            'side',
            'drawn_game',
            'gamelength',
            'meanecho',
            'opponent_nmerror', 'opponent_noblunders',
            'mean_depth_clipped',
            'mean_seldepth',
            'min_nmerror', 'max_nmerror', 'max_meanecho',
            'early_lead',
            'q_error_one', 'q_error_two',
            'opponent_q_error_one', 'opponent_q_error_two',
            'pct_sanemoves',
            'opponent_blunderrate', 'opponent_perfectrate',
            'opponent_grit', 'opponent_meanecho',
            'opponent_mate_created', 'opponent_mate_destroyed',
            'mean_seldepth',
            'mean_depths_ar', 'mean_deepest_ar',
            'opponent_mean_depths_ar', 'opponent_mean_deepest_ar',
            'pct_sanemoves',
           ]

features.extend(dummies)

X = train[features].values
y = train['elo']

gbr = GradientBoostingRegressor(loss='lad', n_estimators=400, min_samples_leaf=10, min_samples_split=50)

msg("CROSS VALIDATING")
cvs = cross_val_score(gbr, X, y, cv=3, n_jobs=-1, scoring='mean_absolute_error')
print cvs

msg("Fitting!")
gbr.fit(X, y)

msg("Saving model")
joblib.dump(gbr, sys.argv[2])

msg("Making predictions for all playergames")
yy_df['gbr_prediction'] = gbr.predict(yy_df[features].values)
yy_df['gbr_error'] = (yy_df['gbr_prediction'] - yy_df['elo']).abs()
yy_df['training'] = yy_df['elo'].notnull()
insample_scores = yy_df.groupby('training')['gbr_error'].agg({'mean' : np.mean, 'median' : np.median, 'stdev': np.std})
print insample_scores


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
submission.write('Event,WhiteElo,BlackElo\\n')
for eventnum in np.arange(25001,50001):
  submission.write('%i,%i,%i\\n' % (eventnum, predictions[eventnum][0], predictions[eventnum][1]))
submission.close()
