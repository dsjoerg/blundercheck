#!/usr/bin/env python

import os, code
import cPickle as pickle
from collections import defaultdict
from djeval import *
import numpy as np
from pandas import DataFrame, Series, read_pickle, concat, cut, qcut
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.externals import joblib

def sample_df(df, n_to_sample):
    if n_to_sample >= len(df.index.values):
        return df
    row_indexes = np.random.choice(df.index.values, n_to_sample, replace=False)
    return df.ix[row_indexes]

def shell():
    vars = globals()
    vars.update(locals())
    shell = code.InteractiveConsole(vars)
    shell.interact()


MG_CLIP = -300

msg('loading blundermodels')
blundermodel_dir = sys.argv[1]
thing = joblib.load(blundermodel_dir + 'groups.p')
elo_bins = thing[0]
mg_quants = thing[1]

print 'elo_bins is %s' % str(elo_bins)
print 'mg_quants is %s' % str(mg_quants)

# perfectmodels[elo_name] = a model fit on a certain ELO range that
# predicts, for a move, the probability that the engine-perfect move
# will be chosen.
perfectmodels = {}

# blundermodels[elo_name, mg_quant] = a model fit on a certain ELO
# range that predicts, for a move, the mg_quant quantile of the
# centipawn error distribution.  mg_quant=0.5 means it's predicting
# the median.
blundermodels = {}

num_models = (len(elo_bins) - 1) * (len(mg_quants) + 1)
msg('Loading the %i models' % num_models)
for modelnum in range(0,num_models):
    thing = joblib.load('%s%i.p' % (blundermodel_dir, modelnum))
    elo_name = thing[0]
    mg_quant = thing[1]
    model = thing[2]
    if mg_quant == 1.0:
        perfectmodels[elo_name] = model
    else:
        blundermodels[elo_name, mg_quant] = model

msg('reading movedata')
moves_df = read_pickle('/data/movedata.p')
moves_df['clipped_movergain'] = moves_df['movergain'].clip(MG_CLIP,0)
train_df = moves_df[moves_df['elo'].notnull()]

features = ['side', 'halfply', 'moverscore', 'bestmove_is_capture', 'bestmove_is_check', 'depth', 'seldepth', 'num_bestmoves', 'num_bestmove_changes', 'bestmove_depths_agreeing', 'deepest_change']

testing = False
if testing:
    games_to_load = 10
    games = np.random.choice(np.arange(1,25001), games_to_load, replace=False)
    train_df = train_df[train_df['gamenum'].isin(games)]

diagnose = False
if diagnose:
    train_df = sample_df(train_df, 1)

perfectcol_names = []
X = train_df[features]
for elo_name, model in perfectmodels.iteritems():
    newcol_name = 'perfect_' + str(elo_name)
    perfectcol_names.append(newcol_name)
    msg('Predicting %s' % newcol_name)
    class_likes = DataFrame(np.log(model.predict_proba(X)))
    if np.isnan(class_likes).sum().sum() > 0:
        print 'WHOA NA'
        print class_likes
    y = (train_df['movergain'] == 0)
    y.index = class_likes.index
    combo = concat([class_likes, y], axis=1)
    train_df[newcol_name] = combo.apply(lambda x: x[1 if x['movergain'] else 0], axis=1).values

# for each game, for each ELO range, compute exp(sum(log-likelihoods))
pggroups = train_df.groupby(['gamenum', 'side', 'elo'])
pm_agg_df = np.exp(pggroups[perfectcol_names[0]].agg({perfectcol_names[0]: sum}))
for pcname in perfectcol_names[1:]:
    pm_agg_df = concat([pm_agg_df, np.exp(pggroups[pcname].agg({pcname: sum}))], axis=1)

# add up the likelihoods across all ELO ranges, add it as a new column
pm_agg_df = concat([pm_agg_df, pm_agg_df[perfectcol_names].sum(axis=1)], axis=1)
pm_agg_df.columns.values[-1] = 'sumlike'

# change the per-ELO-range column to be divided by the sum of likelihoods.
# now it is the probability for that ELO range
for pcname in perfectcol_names:
    pm_agg_df[pcname] = pm_agg_df[pcname] / pm_agg_df['sumlike']

joblib.dump(pm_agg_df, '/data/perfectmove_aggs.p')

if testing:
    print pm_agg_df.sort(axis=1).transpose().head(13)
