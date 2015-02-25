#!/usr/bin/env python

import os
import cPickle as pickle
from djeval import *
from numpy import percentile, arange
from pandas import read_pickle, cut
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.externals import joblib

NUM_ELO_GROUPS = int(sys.argv[1])
NUM_MG_QUANTILES = int(sys.argv[2])
NUM_ESTIMATORS = int(sys.argv[3])
MG_CLIP = -300

msg('splitting ELOs')
eheaders_filename = '/data/eheaders.p'
eheaders_file = open(eheaders_filename, 'r')
eheaders = pickle.load(eheaders_file)
elos = eheaders['elos'].values()
elo_bins = percentile(elos, arange(0, 100. + 1e-9, 100./float(NUM_ELO_GROUPS)))
msg('ELO bins are %s' % str(elo_bins))

msg('reading movedata')
moves_df = read_pickle('/data/movedata.p')
moves_df['clipped_movergain'] = moves_df['movergain'].clip(MG_CLIP,0)
train_df = moves_df[moves_df['elo'].notnull()]
train_df = train_df[train_df['gamenum'] % 2 == 0]
msg('Looking at %i moves' % train_df.shape[0])
train_df['elo_groups'] = cut(train_df['elo'], elo_bins, include_lowest=True)

# we want a certain # of movergain quantile boundaries.  and we want
# them evenly spaced.  but we don't need them for 0 or 1, because we
# already know what the bounds are: they are MG_CLIP and 0.
mg_quants = arange(0, 1. + 1e-9, 1./float(NUM_MG_QUANTILES+1))
mg_quants = mg_quants[1:-1]
msg('we will compute movergain quantiles for %s' % mg_quants)

blundermodel_dir = '/data/blundermodel/'
if not os.path.exists(blundermodel_dir):
    os.makedirs(blundermodel_dir)

joblib.dump([elo_bins, mg_quants], blundermodel_dir + 'groups.p')

modelnum = 0
for elo_name, elo_df in train_df.groupby(train_df['elo_groups']):
    msg('working on elo group %s, of size %i' % (elo_name, elo_df.shape[0]))
    for mg_quant in mg_quants:
        msg('computing mg_quant %f' % mg_quant)
        gbr = GradientBoostingRegressor(loss='quantile', alpha=mg_quant, min_samples_split=500, min_samples_leaf=300, n_estimators=NUM_ESTIMATORS, verbose=1, subsample=0.5, learning_rate=0.2)
        X = elo_df[['side', 'halfply', 'moverscore', 'bestmove_is_capture', 'bestmove_is_check', 'depth', 'seldepth', 'num_bestmoves', 'num_bestmove_changes', 'bestmove_depths_agreeing', 'deepest_change']]
        y = elo_df['clipped_movergain']
        gbr.fit(X, y)
        joblib.dump([elo_name, mg_quant, gbr], '%s%i.p' % (blundermodel_dir, modelnum))
        modelnum = modelnum + 1
