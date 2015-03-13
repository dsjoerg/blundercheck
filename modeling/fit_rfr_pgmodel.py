#!/usr/bin/env python

import sys, time, os
import numpy as np
import cPickle as pickle
from pandas import *
from sklearn.ensemble import RandomForestRegressor
from sklearn.cross_validation import cross_val_score
from sklearn.externals import joblib
from sklearn.metrics import mean_absolute_error
from sklearn.cross_validation import KFold
from sklearn.neighbors import KernelDensity
from sklearn import tree
import pygraphviz as pgv
from StringIO import StringIO
from djeval import *

DO_GB = bool(int(os.environ['DO_GB']))
DO_GOLEM = bool(int(os.environ['DO_GOLEM']))
DO_ERRORCHUNK = bool(int(os.environ['DO_ERRORCHUNK']))
CHAIN_VALIDATE = bool(int(os.environ['CHAIN_VALIDATE']))

n_estimators = int(os.environ['PG_RFR_N_ESTIMATORS'])
n_cv_groups = 3
n_jobs = -1
msl = int(os.environ['PG_RFR_MSL'])
mss = int(os.environ['PG_RFR_MSS'])
multiplier = 1
msl = msl * multiplier
mss = mss * multiplier

msg("Hi, reading yy_df.")
yy_df = read_pickle(sys.argv[1])

msg("Getting subset ready.")
train = yy_df[yy_df.elo.notnull()]

adjust_weights = False
if adjust_weights:
    lower25 = train[train['gamenum'] < 25001]
    upper_50k = train[train['gamenum'] > 50000]

    elo_centuries, elobins = cut(lower25['elo'], 25, retbins=True)
    histthing = lower25.groupby(elo_centuries)['elo'].agg({'count': len})
    histthing['lower'] = elobins[:-1]
    histthing['upper'] = elobins[1:]
    histthing['freq'] = histthing['count'] / sum(histthing['count'] )

    elo_centuries = cut(upper_50k['elo'], bins=elobins)
    upperthing = upper_50k.groupby(elo_centuries)['elo'].agg({'count': len})
    upperthing['up_freq'] = upperthing['count'] / sum(upperthing['count'] )

    freqs = histthing.join(upperthing['up_freq'])
    freqs['localweight'] = freqs['freq'] / freqs['up_freq']

    elo_centuries = cut(train['elo'], bins=elobins)
    elo_centuries.fillna('(1019.14, 1095.4]', inplace=True)
    train['weight'] = freqs.lookup(elo_centuries, ['localweight']*elo_centuries.shape[0])
    train[train['gamenum'] <= 25000]['weight'] = 1.

    upper_50k = train[train['gamenum'] > 50000]
    elo_centuries = cut(upper_50k['elo'], 20)
    msg("Upper weights are: %s" % upper_50k.groupby(elo_centuries)['weight'].agg({'sum': np.sum, 'count': len, 'mean': np.mean}))
else:
    train['weight'] = np.ones(train.shape[0])

use_only_25k = True
if use_only_25k:
    train = train[train['gamenum'] < 25001]
#train = train.loc[:25000]

features = list(yy_df.columns.values)
categorical_features = ['opening_feature']
dummies = get_dummies(yy_df[categorical_features])
elorange_cols = [x for x in list(yy_df.columns.values) if x.startswith('elochunk_')]
elorange_cols.extend([x for x in list(yy_df.columns.values) if x.startswith('opponent_elochunk_')])
material_features = ['material_break_0', 'material_break_1', 'material_break_2', 'material_break_3', 'material_break_4', 'opening_length', 'midgame_length', 'endgame_length', 'mean_acwsa', 'mean_acwsa_0', 'mean_acwsa_1', 'mean_acwsa_2', 'mean_acwsa_3', 'mean_acwsa_4', 'mean_acwsa_5', 'mean_acwsa_6', 'mean_acwsa_7', 'mean_acwsa_8', 'mean_acwsa_9']

excluded_features = ['elo', 'opponent_elo', 'elo_advantage', 'elo_avg', 'winner_elo_advantage', 'ols_error', 'gamenum', 'rfr_prediction', 'rfr_error', 'index', 'level_0']
excluded_features.extend(categorical_features)
#excluded_features.append('ols_prediction')
#excluded_features.extend(dummies)
#excluded_features.extend(material_features)

if not DO_ERRORCHUNK:
    excluded_features.extend(elorange_cols)

if not DO_GB:
    excluded_features.extend(

for f in excluded_features:
    if f in features:
        features.remove(f)
    else:
        print 'Tried to remove %s but it wasnt there' % f

print 'Features are: %s' % features

rfr = RandomForestRegressor(n_estimators=n_estimators, n_jobs=n_jobs, min_samples_leaf=msl, min_samples_split=mss, verbose=1)

do_sklearn_cv = False
if do_sklearn_cv:
    X = train[features].values
    y = train['elo']
    msg("CROSS VALIDATING")
    cvs = cross_val_score(rfr, X, y, cv=n_cv_groups, n_jobs=n_jobs, scoring='mean_absolute_error')
    print cvs, np.mean(cvs)
    sys.stdout.flush()

do_semimanual_cv = False
if do_semimanual_cv:
    msg("fold")
    kf = KFold(train.shape[0], n_folds=n_cv_groups, shuffle=True)
    ins = []
    outs = []
    for train_index, test_index in kf:
            msg("fit")
            foo = rfr.fit(train.iloc[train_index][features], train.iloc[train_index]['elo'])
            msg("pred")
            in_mae = mean_absolute_error(rfr.predict(train.iloc[train_index][features]), train.iloc[train_index]['elo'])
            msg("pred")
            out_preds = rfr.predict(train.iloc[test_index][features])
            out_mae = mean_absolute_error(out_preds, train.iloc[test_index]['elo'])
            for blend in np.arange(0, 1.01, 0.1):
                blended_prediction = (blend * train.iloc[test_index]['ols_prediction']) + ((1.0 - blend) * out_preds)
                blended_score = mean_absolute_error(blended_prediction, train.iloc[test_index]['elo'])
                print blend, blended_score

            print in_mae, out_mae
            sys.stdout.flush()
            ins.append(in_mae)
            outs.append(out_mae)
    print("INS:", ins, np.mean(ins))
    print("OUTS:", outs, np.mean(outs))

do_breadth_cv = True
if do_breadth_cv:
    msg("breadthfold")
    kf = KFold(train.shape[0], n_folds=n_cv_groups, shuffle=True)
    ins = []
    outs = []
    for train_index, test_index in kf:
            msg("fit")
            foo = rfr.fit(train.iloc[train_index][features], train.iloc[train_index]['elo'], sample_weight=train.iloc[train_index]['weight'].values)
            msg("pred")
            in_mae = mean_absolute_error(rfr.predict(train.iloc[train_index][features]), train.iloc[train_index]['elo'])
            msg("pred")
            out_in_25k = train.iloc[test_index]
            out_in_25k = out_in_25k[out_in_25k['gamenum'] < 25001]
            out_preds = rfr.predict(out_in_25k[features])
            out_mae = mean_absolute_error(out_preds, out_in_25k['elo'])
            print in_mae, out_mae
            sys.stdout.flush()
            ins.append(in_mae)
            outs.append(out_mae)
    msg("INS: %s %f" % (ins, np.mean(ins)))
    msg("OUTS: %s %f" % (outs, np.mean(outs)))

if CHAIN_VALIDATE:
    for test_m in [0,1,2]:
        in_df = train[(train['gamenum'] % 3) != test_m]
        out_df = train[(train['gamenum'] % 3) == test_m]
        X = in_df[features].values
        y = in_df['elo']
        msg("fitting using all but group %i" % test_m)
        rfr.fit(X, y)
        pred = rfr.predict(out_df[features].values)
        msg("group %i MAE using model fit on other groups is %f" % (test_m, np.mean((pred - out_df['elo']).abs())))
        

X = train[features].values
y = train['elo']

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

msg("Error summary by gamenum:")
gamenum_centuries = cut(yy_df['gamenum'], 20)
print yy_df.groupby(gamenum_centuries)['rfr_error'].agg({'sum': np.sum, 'count': len, 'mean': np.mean})

msg("Writing yy_df back out with predictions inside")
yy_df.to_pickle(sys.argv[1])

msg("Preparing Kaggle submission")
# map from eventnum to whiteelo,blackelo array

predictions = {}
for eventnum in np.arange(25001,50001):
  predictions[eventnum] = [0,0]

for row in yy_df[yy_df['elo'].isnull()][['gamenum', 'side', 'rfr_prediction']].values:
  eventnum = row[0]
  if eventnum >= 25001 and eventnum <= 50000:
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

print "Feature importances:"
print DataFrame([rfr.feature_importances_, features]).transpose().sort([0], ascending=False)

print "There are %i trees." % len(rfr.estimators_)

dot_data = StringIO()
tree.export_graphviz(rfr.estimators_[0].tree_, out_file=dot_data, feature_names=features)

B=pgv.AGraph(dot_data.getvalue())
B.layout('dot')
B.draw('/data/rfr.png') # draw png

print "Wrote first tree to /data/rfr.png"
