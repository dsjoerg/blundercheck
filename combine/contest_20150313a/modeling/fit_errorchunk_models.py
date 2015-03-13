#!/usr/bin/env python

import os, code
import cPickle as pickle
from djeval import *
import numpy as np
from pandas import read_pickle, cut, concat, Series, get_dummies
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier, ExtraTreesClassifier
from sklearn.cross_validation import StratifiedKFold, cross_val_score
from sklearn.metrics import average_precision_score
from sklearn.externals import joblib
from sklearn.linear_model import LogisticRegression

NUM_ELO_GROUPS = int(sys.argv[1])
NUM_ERRORCHUNKS = int(sys.argv[2])
NUM_ESTIMATORS = int(sys.argv[3])
LOW_BOUND = float(sys.argv[4])
HIGH_BOUND = float(sys.argv[5])

CHAIN_VALIDATE = bool(int(os.environ['CHAIN_VALIDATE']))

n_cv_groups = 2

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
elo_bins = np.percentile(elos, np.arange(0, 100. + 1e-9, 100./float(NUM_ELO_GROUPS)))
msg('ELO bins are %s' % str(elo_bins))

msg('reading movedata')
moves_df = read_pickle('/data/movedata.p')
moves_df['clipped_movergain'] = moves_df['movergain'].clip(-1e9,0)
train_df = moves_df[moves_df['elo'].notnull()]
train_df = train_df[train_df['bestmove_piece'] != False]

if CHAIN_VALIDATE:
    train_df = train_df[train_df['gamenum'] % 3 == 0]

msg('Looking at %i moves' % train_df.shape[0])
train_df['elo_groups'] = cut(train_df['elo'], elo_bins, include_lowest=True)

blundermodel_dir = sys.argv[6]
if not os.path.exists(blundermodel_dir):
    os.makedirs(blundermodel_dir)

categorical_features = ['bestmove_piece', 'bestmove_dir']
dummy_features = []
for index, cf in enumerate(categorical_features):
  dummies = get_dummies(train_df[cf], prefix=cf)
  dummy_features.extend(dummies.columns.values)

features = ['side', 'halfply', 'moverscore', 'bestmove_is_capture', 'bestmove_is_check', 'depth', 'seldepth', 'num_bestmoves', 'num_bestmove_changes', 'bestmove_depths_agreeing', 'deepest_change', 'bestmove_dist', 'prevgain', 'gb', 'gb12']
features.extend(dummy_features)

joblib.dump([elo_bins, chunk_bounds, features], blundermodel_dir + 'groups.p')

# more features you could have:
#  * loss for the 2nd, 3rd, 4th, 5th best move, etc (perfect move is
#    less likely if there are several very close alternatives)

modelnum = 0
for elo_name, elo_df in train_df.groupby(train_df['elo_groups']):
    subset_df = elo_df
    for cb in chunk_bounds:
        msg('working on elo group %s, of size %i. fitting model for error >= %f' % (elo_name, subset_df.shape[0], cb))
        X = subset_df[features]
        y = (subset_df['clipped_movergain'] >= cb)

        rfc = True
        if rfc:
            extra = True
            if extra:
                clf = ExtraTreesClassifier(min_samples_split=200, min_samples_leaf=50, n_jobs=-1, n_estimators=NUM_ESTIMATORS, verbose=1)
            else:
                clf = RandomForestClassifier(min_samples_split=200, min_samples_leaf=50, n_jobs=-1, n_estimators=NUM_ESTIMATORS, verbose=1, oob_score=True)
        else:
            clf = GradientBoostingClassifier(min_samples_split=500, min_samples_leaf=300, n_estimators=NUM_ESTIMATORS, verbose=1, subsample=0.5, learning_rate=0.2)

        msg('CROSS VALIDATING')
        skf = StratifiedKFold(y, n_folds=2, shuffle=True)
        ins = []
        outs = []
        for train_index, test_index in skf:
            foo = clf.fit(X.iloc[train_index], y.iloc[train_index])
            ins.append(average_precision_score(clf.predict(X.iloc[train_index]), y.iloc[train_index]))
            outs.append(average_precision_score(clf.predict(X.iloc[test_index]), y.iloc[test_index]))
        msg("insample  average precision score: %s = %f" % (ins, np.mean(ins)))
        msg("outsample average precision score: %s = %f" % (outs, np.mean(outs)))
        # cvs = cross_val_score(clf, X, y, cv=n_cv_groups, n_jobs=-1, scoring='roc_auc')
        # msg('CV scores: %s = %f' % (cvs, np.mean(cvs)))

        msg('FITTING')
        if CHAIN_VALIDATE:
            fit_df = subset_df[subset_df['gamenum'] % 3 == 0]
            fit_X = fit_df[features]
            fit_y = (fit_df['clipped_movergain'] >= cb)
            clf.fit(fit_X, fit_y)
        else:
            clf.fit(X, y)

        # measure in-sample score
        # measure extent of over-fitting
        # measure model quality in-sample and out-of-sample

        pred_y = clf.predict_proba(X)
        pred_y = [x[1] for x in pred_y]
        combo = concat([Series(y.values), Series(pred_y)], axis=1)
        combo.columns = ['actual', 'predicted']
        combo_groups = cut(combo['predicted'], 10)
        msg("PREDICTION DISTRIBUTION AND SUCCESS:\n%s" % combo.groupby(combo_groups)['actual'].agg({'mean actual': np.mean, 'count': len}))

        msg("FULL INSAMPLE AVERAGE PRECISION SCORE: %f" % average_precision_score(y, pred_y))

        joblib.dump([elo_name, cb, clf], '%s%i.p' % (blundermodel_dir, modelnum))
        modelnum = modelnum + 1
        subset_df = subset_df[~y]
