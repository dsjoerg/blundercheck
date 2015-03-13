#!/usr/bin/env python

import sys, time, code
import numpy as np
import cPickle as pickle
from pandas import DataFrame, read_pickle, get_dummies, cut
import statsmodels.formula.api as sm
from sklearn.externals import joblib
from sklearn.linear_model import LinearRegression

from djeval import *

def shell():
    vars = globals()
    vars.update(locals())
    shell = code.InteractiveConsole(vars)
    shell.interact()


def fix_colname(cn):
    return cn.translate(None, ' ()[],')


msg("Hi, reading yy_df.")
yy_df = read_pickle(sys.argv[1])

# clean up column names
colnames = list(yy_df.columns.values)
colnames = [fix_colname(cn) for cn in colnames]
yy_df.columns = colnames

# change the gamenum and side from being part of the index to being normal columns
yy_df.reset_index(inplace=True)

msg("Getting subset ready.")

# TODO save the dummies along with yy_df
categorical_features = ['opening_feature']
dummies = get_dummies(yy_df[categorical_features])

elorange_cols = [x for x in list(yy_df.columns.values) if x.startswith('elochunk_')][:-1]
elorange_cols.extend([x for x in list(yy_df.columns.values) if x.startswith('opponent_elochunk_')][:-1])

#gb_cols = [colname for colname in colnames if colname.startswith('gb_')]
gb_cols = ['gb_mean', 'gb_mean_permove', 'gb_num_15', 'gb_permove_15']

# TODO save the moveelo_features along with yy_df
moveelo_features = [("moveelo_" + x) for x in ['mean', 'median', '25', '10', 'min', 'max', 'stdev']]

new_depth_cols = ['mean_num_bestmoves', 'mean_num_bestmove_changes', 'mean_bestmove_depths_agreeing', 'mean_deepest_change', 'mean_deepest_change_ratio']
stdev_cols = ['stdeverror', 'opponent_stdeverror', 'stdevpos']
material_features = ['material_break_0', 'mean_acwsa']

train = yy_df[yy_df.meanerror.notnull() & yy_df.elo.notnull()]

use_only_25k = True
if use_only_25k:
    train = train[train['gamenum'] < 25001]

chain_validating = False
if chain_validating:
    train = train[train['gamenum'] % 3 == 0]

formula_rhs = "side + nmerror + gameoutcome + drawn_game + gamelength + meanecho"
formula_rhs = formula_rhs + " + opponent_nmerror + opponent_noblunders"
formula_rhs = formula_rhs + " + min_nmerror + early_lead"
formula_rhs = formula_rhs + " + q_error_one + q_error_two"
formula_rhs = formula_rhs + " + opponent_q_error_one"
formula_rhs = formula_rhs + " + mean_depth_clipped + mean_seldepth"
formula_rhs = formula_rhs + " + mean_depths_agreeing_ratio + mean_deepest_agree_ratio"
formula_rhs = formula_rhs + " + opponent_mean_depths_agreeing_ratio + opponent_mean_deepest_agree_ratio"
formula_rhs = formula_rhs + " + pct_sanemoves"
formula_rhs = formula_rhs + " + " + " + ".join(dummies.columns.values)
formula_rhs = formula_rhs + " + " + " + ".join(new_depth_cols)
formula_rhs = formula_rhs + " + " + " + ".join(stdev_cols)
formula_rhs = formula_rhs + " + final_elo + final_ply + final_num_games + final_elo_stdev + elopath_min + elopath_max"
formula_rhs = formula_rhs + " + pos_fft_1 "
formula_rhs = formula_rhs + " + final_elo_elo4 + final_ply_elo4 + final_num_games_elo4 + final_elo_stdev_elo4"
formula_rhs = formula_rhs + " + final_elo_elo10 + final_ply_elo10 + final_num_games_elo10 + final_elo_stdev_elo10"
formula_rhs = formula_rhs + " + moveelo_weighted"
formula_rhs = formula_rhs + " + " + " + ".join(material_features)

if False:
    formula_rhs = formula_rhs + " + " + " + ".join(gb_cols)
    formula_rhs = formula_rhs + " + " + " + ".join(elorange_cols)

# hey lets just use the elorange columns and see how they do
#formula_rhs = " + ".join(elorange_cols)


msg("Fitting!")

weights = np.ones(train.shape[0])

formula = "elo_avg ~ " + formula_rhs
ols_avg = sm.wls(formula=formula, data=train, weights=weights).fit()
print ols_avg.summary()

formula = "elo_advantage ~ " + formula_rhs
ols_ea = sm.wls(formula=formula, data=train, weights=weights).fit()
print ols_ea.summary()


msg("Making predictions for all playergames")
yy_df['ols_avg_prediction'] = ols_avg.predict(yy_df)
yy_df['ols_ea_prediction'] = ols_ea.predict(yy_df)

yy_df['ols_avg_error'] = (yy_df['ols_avg_prediction'] - yy_df['elo_avg']).abs()
yy_df['ols_ea_error'] = (yy_df['ols_ea_prediction'] - yy_df['elo_advantage']).abs()
yy_df['training'] = (yy_df['gamenum'] % 3)
insample_scores = yy_df.groupby('training')['ols_avg_error'].agg({'mean' : np.mean, 'median' : np.median, 'stdev': np.std})
print insample_scores
insample_scores = yy_df.groupby('training')['ols_ea_error'].agg({'mean' : np.mean, 'median' : np.median, 'stdev': np.std})
print insample_scores

msg("Error summary by ELO:")
elo_centuries = cut(yy_df['elo'], 20)
print yy_df.groupby(elo_centuries)['ols_avg_error'].agg({'sum': np.sum, 'count': len, 'mean': np.mean})
print yy_df.groupby(elo_centuries)['ols_ea_error'].agg({'sum': np.sum, 'count': len, 'mean': np.mean})

msg("Error summary by gamenum:")
gamenum_centuries = cut(yy_df['gamenum'], 20)
print yy_df.groupby(gamenum_centuries)['ols_avg_error'].agg({'sum': np.sum, 'count': len, 'mean': np.mean})
print yy_df.groupby(gamenum_centuries)['ols_ea_error'].agg({'sum': np.sum, 'count': len, 'mean': np.mean})

msg("Writing yy_df back out with ols predictions inside")
yy_df.to_pickle(sys.argv[1])
