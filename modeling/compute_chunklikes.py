#!/usr/bin/env python

import os, code
import cPickle as pickle
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

msg('loading chunklikes')
blundermodel_dir = sys.argv[1]
thing = joblib.load(blundermodel_dir + 'groups.p')
elo_bins = thing[0]
chunk_bounds = thing[1]

print 'elo_bins is %s' % str(elo_bins)
print 'chunk_bounds is %s' % str(chunk_bounds)

# chunkmodels[elo_name, chunk_bound] = a model fit on a certain ELO
# range that predicts, for a move, given that the error was < than the
# previous chunk bounds, the chance that the error will be >= this
# chunk bound.
chunkmodels = {}

num_models = (len(elo_bins) - 1) * len(chunk_bounds)
elo_names = set()
msg('Loading the %i models' % num_models)
for modelnum in range(0,num_models):
    thing = joblib.load('%s%i.p' % (blundermodel_dir, modelnum))
    elo_name = thing[0]
    elo_names.add(elo_name)
    chunk_bound = thing[1]
    model = thing[2]
    chunkmodels[elo_name, chunk_bound] = model

msg('reading movedata')
moves_df = read_pickle('/data/movedata.p')
moves_df['clipped_movergain'] = moves_df['movergain'].clip(-1e9,0)
train_df = moves_df[moves_df['elo'].notnull()]

features = ['side', 'halfply', 'moverscore', 'bestmove_is_capture', 'bestmove_is_check', 'depth', 'seldepth', 'num_bestmoves', 'num_bestmove_changes', 'bestmove_depths_agreeing', 'deepest_change']

testing = False
if testing:
    games_to_load = 10
    games = np.random.choice(np.arange(1,25001), games_to_load, replace=False)
    train_df = train_df[train_df['gamenum'].isin(games)]

diagnose = False
if diagnose:
    train_df = sample_df(train_df, 30)

validating = True
if validating:
    train_df = train_df[train_df['gamenum'] % 2 == 0]

like_colnames = []
X = train_df[features]

# given a single row of sequential conditional likelihoods,
# return the likelihood for the actual move that was made
def gain_likelihood(row):
    mg = row['movergain']
    prob = 1.0
    for ix, cb in enumerate(chunk_bounds):
        if mg >= cb:
            return prob * row.iloc[ix]
        else:
            prob = prob * (1 - row.iloc[ix])
    return prob
    

for elo_name in list(elo_names):
    allchunks = []
    for cb in chunk_bounds:
        model = chunkmodels[elo_name, cb]
        newcol_name = 'cb_' + str(elo_name.translate(None, ' ()[],')) + '_' + str(cb)
        like_colnames.append(newcol_name)
        msg('Predicting %s' % newcol_name)
        preds = model.predict_proba(X)
        preds_series = DataFrame(preds).iloc[:,1]
        preds_series.index = X.index
        preds_series.name = cb
        allchunks.append(preds_series)
        
    allchunks.append(train_df['movergain'])
    allchunks_df = concat(allchunks, axis=1)
    train_df[elo_name] = allchunks_df.apply(gain_likelihood, axis=1)

if diagnose:
    cols_to_show = list(elo_names)
    cols_to_show.extend(['gamenum','side','halfply','elo','movergain'])
    print train_df[cols_to_show].transpose()

# group by player-game, and combine all the likelihoods into a single
# likelihood for that ELO

def exp_sum_log(foo):
    return np.exp(sum(np.log(foo)))

# for each player-game, for each ELO range, compute product of likelihoods for all moves 
# in that game.  
chunkgroups = train_df.groupby(['gamenum', 'side', 'elo'])
ch_aggs = []
# exp(sum(log(likelihoods))) is just a cute way to do
# product(likelihoods) which is *maybe* more numerically friendly
for elo_name in elo_names:
    ch_aggs.append( chunkgroups[elo_name].agg({elo_name: lambda x: np.exp(sum(np.log(x)))}) )
ch_agg_df = concat(ch_aggs, axis=1)

# add up the likelihoods across all ELO ranges, add it as a new column
ch_agg_df = concat([ch_agg_df, ch_agg_df[list(elo_names)].sum(axis=1)], axis=1)
ch_agg_df.columns.values[-1] = 'sumlike'

# change the per-ELO-range column to be divided by the sum of likelihoods.
# now it is the probability for that ELO range
for elo_name in elo_names:
    ch_agg_df[elo_name] = ch_agg_df[elo_name] / ch_agg_df['sumlike']
ch_agg_df.drop('sumlike', axis=1, inplace=True)

if testing:
    print ch_agg_df

joblib.dump(ch_agg_df, '/data/chunk_aggs.p')
