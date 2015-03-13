#!/usr/bin/env python

import sys, time, code
import numpy as np
import cPickle as pickle
from pandas import DataFrame, read_pickle, get_dummies, cut
import statsmodels.formula.api as sm
from sklearn.externals import joblib
from sklearn.linear_model import LinearRegression, Ridge, RidgeCV, LassoCV
from djeval import *


DO_GB = bool(os.environ['DO_GB'])
DO_GOLEM = bool(os.environ['DO_GOLEM'])
DO_ERRORCHUNK = bool(os.environ['DO_ERRORCHUNK'])
CHAIN_VALIDATE = bool(os.environ['CHAIN_VALIDATE'])

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

if 'level_0' in colnames:
    yy_df.drop('level_0', axis=1, inplace=True)

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

if CHAIN_VALIDATE:
    train = train[train['gamenum'] % 3 == 0]

golem_cols = [
'final_elo',
'final_ply',
'final_num_games',
'final_elo_stdev',
'elopath_min',
'elopath_max',
'final_elo_elo4',
'final_ply_elo4',
'final_num_games_elo4',
'final_elo_stdev_elo4',
'final_elo_elo10',
'final_ply_elo10',
'final_num_games_elo10',
'final_elo_stdev_elo10',
]    

rhs_cols = [
'side',
'nmerror',
'gameoutcome',
'drawn_game',
'gamelength',
'meanecho',
'opponent_nmerror',
'opponent_noblunders',
'min_nmerror',
'early_lead',
'q_error_one',
'q_error_two',
'opponent_q_error_one',
'mean_depth_clipped',
'mean_seldepth',
'mean_depths_agreeing_ratio',
'mean_deepest_agree_ratio',
'opponent_mean_depths_agreeing_ratio',
'opponent_mean_deepest_agree_ratio',
'pct_sanemoves',
'pos_fft_1',
'moveelo_weighted',
]

rhs_cols.extend(dummies.columns.values)
rhs_cols.extend(new_depth_cols)
rhs_cols.extend(stdev_cols)
rhs_cols.extend(material_features)

if DO_GOLEM:
    rhs_cols.extend(golem_cols)

if DO_GB:
    formula_rhs = formula_rhs + " + " + " + ".join(gb_cols)

if DO_ERRORCHUNK:
    formula_rhs = formula_rhs + " + " + " + ".join(elorange_cols)

# hey lets just use the elorange columns and see how they do
#formula_rhs = " + ".join(elorange_cols)

formula = "elo ~ " + " + ".join(rhs_cols)

msg("Fitting!")

weights = np.ones(train.shape[0])

do_statsmodels=True
if do_statsmodels:
    ols = sm.wls(formula=formula, data=train, weights=weights).fit()
    print ols.summary()
    msg("Making predictions for all playergames")
    yy_df['ols_prediction'] = ols.predict(yy_df)
else:
    ols_lr = LassoCV(n_jobs=-1, verbose=True)
    X = train[rhs_cols]
    y = train['elo']
    ols_lr.fit(X,y)
    yy_df['ols_prediction'] = ols_lr.predict(X)

yy_df['ols_error'] = (yy_df['ols_prediction'] - yy_df['elo']).abs()
yy_df['training'] = (yy_df['gamenum'] % 3)
insample_scores = yy_df.groupby('training')['ols_error'].agg({'mean' : np.mean, 'median' : np.median, 'stdev': np.std})
print insample_scores

msg("Error summary by ELO:")
elo_centuries = cut(yy_df['elo'], 20)
print yy_df.groupby(elo_centuries)['ols_error'].agg({'sum': np.sum, 'count': len, 'mean': np.mean})

msg("Error summary by gamenum:")
gamenum_centuries = cut(yy_df['gamenum'], 20)
print yy_df.groupby(gamenum_centuries)['ols_error'].agg({'sum': np.sum, 'count': len, 'mean': np.mean})

msg("Writing yy_df back out with ols predictions inside")
yy_df.to_pickle(sys.argv[1])
