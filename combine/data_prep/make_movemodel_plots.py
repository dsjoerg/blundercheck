#!/usr/bin/env python

import matplotlib
matplotlib.use('Agg') # Must be before importing matplotlib.pyplot or pylab!

import sys
import seaborn as sns
from pandas import read_pickle, qcut
from itertools import product
import matplotlib.pyplot as plt
from pandas import get_dummies
from pandas import groupby
from pandas import DataFrame
import numpy as np
from djeval import *
from sklearn.externals import joblib
from sklearn.ensemble.partial_dependence import plot_partial_dependence
from sklearn.ensemble.partial_dependence import partial_dependence

msg("Hello there, reading moves_df.")
moves_df = read_pickle('/data/movedata.p')
moves_df = moves_df[0:60000]

msg("Hello there, reading rfr.")
rfr, features_to_use = joblib.load('/data/movemodel.p')

PREDICT_N = 400000
FITTING_N = 50000

def predict_move_elos():
    all_y_preds = []
    all_y_stds = []
    moves_df['abs_moverscore'] = moves_df['moverscore'].abs()
    for i in range(0, len(moves_df) + PREDICT_N, PREDICT_N):
        predict_df = moves_df.iloc[i : i + PREDICT_N]
        predict_features = predict_df[features_to_use]
        print("Predicting for chunk %i" % i)
        y_pred, y_std = rfr.predict(predict_features, with_std=True)
        all_y_preds.append(y_pred)
        all_y_stds.append(y_std)
    moves_df['elo_predicted'] = np.concatenate(all_y_preds)
    moves_df['elo_pred_std'] = np.concatenate(all_y_stds)
    moves_df['elo_pred_std'].fillna(40, inplace=True)
    moves_df['elo_pred_weight'] = 1. / (moves_df['elo_pred_std'] * moves_df['elo_pred_std'])
    moves_df['elo_weighted_pred'] = moves_df['elo_pred_weight'] * moves_df['elo_predicted']

msg("Predicting move ELOs")
predict_move_elos()

moves_df['elo_residual'] = (moves_df['elo_predicted'] - moves_df['elo'])
with_elo = moves_df[moves_df['elo'].notnull()]
with_elo = with_elo[0:50000]

#num_features_to_plot = 4
#features_to_plot = list(DataFrame([rfr.feature_importances_, features_to_use]).transpose().sort([0], ascending=False)[1][0:num_features_to_plot])

with_elo['log_movergain'] = np.log((-1 * with_elo['movergain']).clip(1,50000))
with_elo['log_abs_moverscore'] = np.log(with_elo['abs_moverscore'].clip(1,50000))

features_to_plot = ['log_movergain', 'log_abs_moverscore', 'halfply', 'sd_ratio', 'depths_ar', 'seldepth', 'deepest_change', 'bestmove_depths_agreeing', 'deepest_ar', 'deepest_agree', 'num_bestmove_changes']
features_to_plot = ['log_movergain']
plottables = ['elo', 'elo_predicted', 'elo_residual']

for a, b in product(features_to_plot, plottables):
    msg('Making %s %s' % (a, b))
    x = with_elo[a]
    y = with_elo[b]
    msg('type = %s' % x.dtype)
    if x.dtype == 'object':
        plt.figure()
        x.value_counts().plot(kind='bar')
        plt.savefig('/data/movemodel_' + a + '_hist.png')
        plt.close('all')
    else:
        try:
            xlim = tuple(np.percentile(x, [1,99]))
            ylim = tuple(np.percentile(y, [1,99]))
            with sns.axes_style("white"):
                sns.jointplot(x, y, kind="hex", xlim=xlim, ylim=ylim)
            plt.savefig('/data/movemodel_scatter_' + a + '_' + b + '.png')
            plt.close('all')
        except:
    #        sns.violinplot(x, y)
    #        plt.savefig('/data/' + a + '_' + b + '.png')
    #        plt.close()
            plt.figure()
            x.plot(kind='hist')
            plt.savefig('/data/movemodel_' + a + '_hist.png')
            plt.close('all')
