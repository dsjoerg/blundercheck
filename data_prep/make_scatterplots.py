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
import numpy as np
from djeval import *

sns.set_palette("deep", desat=.6)
sns.set_context(rc={"figure.figsize": (8, 4)})

def percentile_subset(x, min_pct, max_pct):
    min_value, max_value = np.percentile(x, [min_pct, max_pct])
    return x[(x >= min_value) & (x <= max_value)]

msg("Hello there, reading yy_df.")
yy_df = read_pickle(sys.argv[1])


with_elo = yy_df[yy_df['elo'].notnull()]

features = list(yy_df.columns.values)

# blunderrate graph looks terrible because its bin edges are: [ 0.        ,  0.        ,  0.        ,  0.        ,  0.01960784, 0.03125   ,  0.04651163,  0.06666667,  0.09090909,  0.12820513,        0.83333333]

plottables = ['elo', 'gbr_prediction', 'gbr_error']
plottables = ['elo']
#features = ['opening_feature']

# this wasnt working for some reason
make_pairplot = False
if make_pairplot:
    g = sns.pairplot(with_elo[plottables], size=2.5)
    plt.savefig('/data/pairplot.png')
    plt.close()

for a, b in product(features, plottables):
    msg('Making %s %s' % (a, b))
    x = with_elo[a]
    y = with_elo[b]
    msg('type = %s' % x.dtype)
    if x.dtype == 'object':
        plt.figure()
        x.value_counts().plot(kind='bar')
        plt.savefig('/data/' + a + '_hist.png')
        plt.close()
    else:
        try:
            xlim = tuple(np.percentile(x, [1,99]))
            ylim = tuple(np.percentile(y, [1,99]))
            with sns.axes_style("white"):
                sns.jointplot(x, y, kind="hex", xlim=xlim, ylim=ylim)
            plt.savefig('/data/scatter_' + a + '_' + b + '.png')
            plt.close()
        except:
    #        sns.violinplot(x, y)
    #        plt.savefig('/data/' + a + '_' + b + '.png')
    #        plt.close()
            plt.figure()
            x.plot(kind='hist')
            plt.savefig('/data/' + a + '_hist.png')
            plt.close()

do_indivs = True
if do_indivs:
    for a, b in product(features, plottables):
        msg('Making %s %s' % (a, b))
        try:
            plt.figure()
            groupings, bins = qcut(with_elo[a], 10, labels=False, retbins=True)
            sns.violinplot(with_elo[b], groupings)
            plt.savefig('/data/' + a + '_' + b + '.png')
            plt.close()
        except:
            try:
                plt.figure()
                sns.violinplot(with_elo[b], with_elo[a])
                plt.savefig('/data/' + a + '_' + b + '.png')
                plt.close()
            except:
                msg("Couldnt manage for %s %s" % (a, b))

    #        f, ax = plt.subplots(figsize=(11, 6))
    #        sns.violinplot(with_elo[second], groupings, names=[str(b) + str(b+1) for b in bins[:-1]])
    #        ax.set(ylim=(-.7, 1.05))
    #        sns.despine(left=True, bottom=True)
