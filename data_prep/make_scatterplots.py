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

features = ['nmerror',
            'blunderrate', 'noblunders', 
            'perfectrate',
            'gameoutcome',
            'won_by_checkmate', 'lost_by_checkmate', 'ended_by_checkmate',
            'my_final_equity', 'final_equity',
            'grit', 'any_grit', 'opponent_any_grit', 'major_grit',
            'mate_created', 'mate_destroyed', 'premature_quit',
            'side',
            'drawn_game',
            'gamelength',
            'meanecho',
            'opponent_nmerror', 'opponent_noblunders',
            'mean_depth_clipped',
            'mean_seldepth',
            'min_nmerror', 'max_nmerror', 'max_meanecho',
            'early_lead',
            'q_error_one', 'q_error_two',
            'opponent_q_error_one', 'opponent_q_error_two',
            'pct_sanemoves',
            'opponent_blunderrate', 'opponent_perfectrate',
            'opponent_grit', 'opponent_meanecho',
            'opponent_mate_created', 'opponent_mate_destroyed',
            'mean_seldepth',
            'mean_depths_ar', 'mean_deepest_ar',
            'opponent_mean_depths_ar', 'opponent_mean_deepest_ar',
            'pct_sanemoves',
            'moveelo_weighted'
           ]

plottables = ['elo', 'gbr_prediction', 'gbr_error']
plottables.extend(['gamelength', 'mean_depth_clipped', 'mean_deepest_ar', 'opponent_mean_deepest_ar'])

for a, b in combinations(plottables, 2):
    for first, second in [(a,b), (b,a)]:
        try:
            groupings, bins = qcut(with_elo[first], 10, labels=False, retbins=True)
            sns.violinplot(with_elo[second], groupings)
            plt.savefig('/data/' + first + '_' + second + '.png')
            plt.close()
        except:
            print("Couldnt manage for %s %s" % (first, second))

#        f, ax = plt.subplots(figsize=(11, 6))
#        sns.violinplot(with_elo[second], groupings, names=[str(b) + str(b+1) for b in bins[:-1]])
#        ax.set(ylim=(-.7, 1.05))
#        sns.despine(left=True, bottom=True)
        print '.',
        sys.stdout.flush()


g = sns.PairGrid(with_elo[plottables])
g.map_diag(plt.hist)
g.map_offdiag(plt.scatter)
g.add_legend()
plt.savefig('/data/pairgrid.png')
plt.close()
