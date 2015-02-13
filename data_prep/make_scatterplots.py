#!/usr/bin/env python

import matplotlib
matplotlib.use('Agg') # Must be before importing matplotlib.pyplot or pylab!

import sys
import seaborn as sns
from pandas import read_pickle, qcut
from itertools import product
import matplotlib.pyplot as plt
from pandas import get_dummies
from djeval import *

sns.set_palette("deep", desat=.6)
sns.set_context(rc={"figure.figsize": (8, 4)})

msg("Hello there, reading yy_df.")
yy_df = read_pickle(sys.argv[1])


with_elo = yy_df[yy_df['elo'].notnull()]

features = list(yy_df.columns.values)

# blunderrate graph looks terrible because its bin edges are: [ 0.        ,  0.        ,  0.        ,  0.        ,  0.01960784, 0.03125   ,  0.04651163,  0.06666667,  0.09090909,  0.12820513,        0.83333333]

plottables = ['elo', 'gbr_prediction', 'gbr_error']

do_indivs = False
if do_indivs:
    for a, b in product(features, plottables):
        msg('.')
        try:
            groupings, bins = qcut(with_elo[a], 10, labels=False, retbins=True)
            sns.violinplot(with_elo[b], groupings)
            plt.savefig('/data/' + a + '_' + b + '.png')
            plt.close()
        except:
            try:
                sns.violinplot(with_elo[b], with_elo[a])
                plt.savefig('/data/' + a + '_' + b + '.png')
                plt.close()
            except:
                msg("Couldnt manage for %s %s" % (a, b))

    #        f, ax = plt.subplots(figsize=(11, 6))
    #        sns.violinplot(with_elo[second], groupings, names=[str(b) + str(b+1) for b in bins[:-1]])
    #        ax.set(ylim=(-.7, 1.05))
    #        sns.despine(left=True, bottom=True)

# this wasnt working for some reason
make_pairplot = False
if make_pairplot:
    g = sns.pairplot(with_elo[plottables], size=2.5)
    plt.savefig('/data/pairplot.png')
    plt.close()

for a, b in product(features, plottables):
    msg('.')
    x = yy_df[a]
    y = yy_df[b]
    with sns.axes_style("white"):
        sns.jointplot(x, y, kind="hex")
    plt.savefig('/data/scatter_' + a + '_' + b + '.png')
    plt.close()
