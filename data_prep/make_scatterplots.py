#!/usr/bin/env python

import sys
import seaborn as sns
from pandas import read_pickle
from matplotlib import savefig

sns.set_palette("deep", desat=.6)
sns.set_context(rc={"figure.figsize": (8, 4)})

msg("Hi, reading yy_df.")
yy_df = read_pickle(sys.argv[1])

x = yy_df['nmerror']
y = yy_df['elo']
with sns.axes_style("white"):
    sns.jointplot(x, y, kind="hex")
savefig('/data/seaborn.png')
