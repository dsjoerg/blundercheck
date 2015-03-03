#!/usr/bin/env python

import os
import cPickle as pickle
from djeval import *
import numpy as np
from pandas import DataFrame, Series, read_pickle, concat, cut, qcut
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.externals import joblib

MG_CLIP = -300

def quantile_scorer_two(estimator, X, y):
    pred_y = estimator.predict(X)
    print DataFrame([X['elo'], y, pred_y])
    mask = y < pred_y
    return float(mask.sum()) / y.shape[0]

msg('loading blundermodels')
blundermodel_dir = sys.argv[1]
thing = joblib.load(blundermodel_dir + 'groups.p')
elo_bins = thing[0]
mg_quants = thing[1]

print 'elo_bins is %s' % str(elo_bins)
print 'mg_quants is %s' % str(mg_quants)

blundermodels = {}
num_models = (len(elo_bins) - 1) * (len(mg_quants) + 1)
msg('Loading the %i models' % num_models)
for modelnum in range(0,num_models):
    thing = joblib.load('%s%i.p' % (blundermodel_dir, modelnum))
    elo_name = thing[0]
    mg_quant = thing[1]
    model = thing[2]
    blundermodels[elo_name, mg_quant] = model

msg('reading movedata')
moves_df = read_pickle('/data/movedata.p')
moves_df['clipped_movergain'] = moves_df['movergain'].clip(MG_CLIP,0)
train_df = moves_df[moves_df['elo'].notnull()]
fitted_df = train_df[train_df['gamenum'] % 2 == 0]
test_df = train_df[train_df['gamenum'] % 2 == 1]

features = ['side', 'halfply', 'moverscore', 'bestmove_is_capture', 'bestmove_is_check', 'depth', 'seldepth', 'num_bestmoves', 'num_bestmove_changes', 'bestmove_depths_agreeing', 'deepest_change']

for key, model in blundermodels.iteritems():
    elo_name = key[0]
    mg_quant = key[1]

    elo_bounds = [float(x) for x in elo_name[1:-1].split(', ')]
    moves_to_test = fitted_df[(fitted_df['elo'] >= elo_bounds[0]) & (fitted_df['elo'] <= elo_bounds[1])]
    diagnostic_cols_to_show = ['gamenum','elo','perfect_pred','movergain']
    diagnostic_cols_to_show.extend(features)

    if mg_quant == 1.0:
        X = moves_to_test[features]
        y = (moves_to_test['clipped_movergain'] == 0)
        pred_y = model.predict_proba(X)
        pred_y = [x[1] for x in pred_y]
        combo = concat([Series(y.values), Series(pred_y)], axis=1)
        combo_groups = cut(combo[1], 10)
        print("%s perfect-move model prediction distribution and success:\n%s" % (elo_name, combo.groupby(combo_groups)[0].agg({'mean': np.mean, 'count': len})))
        moves_to_test['perfect_pred'] = pred_y
        print "MOVES MOST LIKELY TO MAKE THE BEST MOVE:"
        print moves_to_test.sort('perfect_pred', ascending=False)[diagnostic_cols_to_show].head()
        print "MOVES LEAST LIKELY TO MAKE THE BEST MOVE:"
        print moves_to_test.sort('perfect_pred', ascending=True)[diagnostic_cols_to_show].head()

    else:
        imperfect_moves = moves_to_test[moves_to_test['clipped_movergain'] < 0]
        X = imperfect_moves[features]
        y = imperfect_moves['clipped_movergain']
        pred_y = model.predict(X)
        mask = y < pred_y
        score = float(mask.sum()) / y.shape[0]
        print('imperfect-move error-size quantile model for %s: true quantile is %f' % (key, score))
        combo = concat([Series(y.values), Series(pred_y)], axis=1)
        combo_groups = qcut(combo[1], 10)
        combo_stats = combo.groupby(combo_groups)[0].agg({'mean': np.mean, 'q': lambda x: np.percentile(x, float(mg_quant) * 100), 'count': len})
        print("%s distribution of error by prediction range:\n%s" % (elo_name, combo_stats))
