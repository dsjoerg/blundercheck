#!/usr/bin/env python

import matplotlib
matplotlib.use('Agg') # Must be before importing matplotlib.pyplot or pylab!

import sys
import seaborn as sns
from pandas import read_pickle, qcut
import matplotlib.pyplot as plt
from djeval import *

sns.set_palette("deep", desat=.6)
sns.set_context(rc={"figure.figsize": (8, 4)})

msg("Hiiii, reading yy_df.")
yy_df = read_pickle(sys.argv[1])

x = yy_df['nmerror']
y = yy_df['elo']
with sns.axes_style("white"):
    sns.jointplot(x, y, kind="hex")
plt.savefig('/data/seaborn.png')
plt.close()

with_elo = yy_df[yy_df['elo'].notnull()]
with_elo['nmerror_deciles'], bins = qcut(with_elo['nmerror'], 10, labels=False, retbins=True)
#grp = with_elo.groupby('nmerror_deciles')['elo']
sns.violinplot(with_elo['elo'], with_elo['nmerror_deciles'])
plt.savefig('/data/seaborn_violin.png')
