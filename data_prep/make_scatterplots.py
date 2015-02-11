#!/usr/bin/env python

import matplotlib
matplotlib.use('Agg') # Must be before importing matplotlib.pyplot or pylab!

import sys
import seaborn as sns
from pandas import read_pickle, qcut
from itertools import combinations
import matplotlib.pyplot as plt
from djeval import *

sns.set_palette("deep", desat=.6)
sns.set_context(rc={"figure.figsize": (8, 4)})

msg("Hello there, reading yy_df.")
yy_df = read_pickle(sys.argv[1])

x = yy_df['nmerror']
y = yy_df['elo']
with sns.axes_style("white"):
    sns.jointplot(x, y, kind="hex")
plt.savefig('/data/seaborn.png')
plt.close()

with_elo = yy_df[yy_df['elo'].notnull()]

plottables = ['nmerror', 'elo', 'gbr_prediction', 'gbr_error']
for a, b in combinations(plottables, 2):
    for first, second in [(a,b), (b,a)]:
        groupings, bins = qcut(with_elo[first], 10, labels=False, retbins=True)
        f, ax = plt.subplots(figsize=(11, 6))
        sns.violinplot(with_elo[second], groupings, names=[str(b) + str(b+1) for b in bins[:-1]])
        ax.set(ylim=(-.7, 1.05))
        sns.despine(left=True, bottom=True)
        plt.savefig('/data/' + first + '_' + second + '.png')
        plt.close()
        print '.',
