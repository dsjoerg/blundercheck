#!/usr/bin/env python

import os, code
import cPickle as pickle
from djeval import *
from numpy import percentile, arange
from pandas import read_pickle, cut
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.externals import joblib

NUM_ELO_GROUPS = int(sys.argv[1])
NUM_ERRORCHUNKS = int(sys.argv[2])
NUM_ESTIMATORS = int(sys.argv[3])
LOW_BOUND = float(sys.argv[4])
HIGH_BOUND = float(sys.argv[5])

def shell():
    vars = globals()
    vars.update(locals())
    shell = code.InteractiveConsole(vars)
    shell.interact()

chunk_spacing_factor = (HIGH_BOUND / LOW_BOUND) ** (1/(float(NUM_ERRORCHUNKS)-1.))
chunk_bounds = [-1. * LOW_BOUND * (chunk_spacing_factor ** i) for i in range(0,NUM_ERRORCHUNKS)]
chunk_bounds.insert(0, 0.)
msg('errorchunk bounds are %s' % chunk_bounds)


msg('splitting ELOs')
eheaders_filename = '/data/eheaders.p'
eheaders_file = open(eheaders_filename, 'r')
eheaders = pickle.load(eheaders_file)
elos = eheaders['elos'].values()
elo_bins = percentile(elos, arange(0, 100. + 1e-9, 100./float(NUM_ELO_GROUPS)))
msg('ELO bins are %s' % str(elo_bins))

msg('reading movedata')
moves_df = read_pickle('/data/movedata.p')
moves_df['clipped_movergain'] = moves_df['movergain'].clip(-1e9,0)
train_df = moves_df[moves_df['elo'].notnull()]

validating = True
if validating:
    train_df = train_df[train_df['gamenum'] % 2 == 0]

msg('Looking at %i moves' % train_df.shape[0])
train_df['elo_groups'] = cut(train_df['elo'], elo_bins, include_lowest=True)

blundermodel_dir = sys.argv[6]
if not os.path.exists(blundermodel_dir):
    os.makedirs(blundermodel_dir)

joblib.dump([elo_bins, chunk_bounds], blundermodel_dir + 'groups.p')
features = ['side', 'halfply', 'moverscore', 'bestmove_is_capture', 'bestmove_is_check', 'depth', 'seldepth', 'num_bestmoves', 'num_bestmove_changes', 'bestmove_depths_agreeing', 'deepest_change']

modelnum = 0
for elo_name, elo_df in train_df.groupby(train_df['elo_groups']):
    subset_df = elo_df
    for cb in chunk_bounds:
        msg('working on elo group %s, of size %i. fitting model for error >= %f' % (elo_name, subset_df.shape[0], cb))
        X = subset_df[features]
        y = (subset_df['clipped_movergain'] >= cb)
        
        rfr = True
        if rfr:
            clf = RandomForestClassifier(min_samples_split=500, min_samples_leaf=300, n_estimators=NUM_ESTIMATORS, verbose=1, njobs=-1)
        else:
            clf = GradientBoostingClassifier(min_samples_split=500, min_samples_leaf=300, n_estimators=NUM_ESTIMATORS, verbose=1, subsample=0.5, learning_rate=0.2)

        clf.fit(X, y)
        joblib.dump([elo_name, cb, clf], '%s%i.p' % (blundermodel_dir, modelnum))
        modelnum = modelnum + 1
        subset_df = subset_df[~y]
