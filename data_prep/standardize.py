#!/usr/bin/env python

import sys, time, code
import numpy as np
from pandas import DataFrame, read_pickle
from sklearn.preprocessing import StandardScaler

from djeval import *

def shell():
    vars = globals()
    vars.update(locals())
    shell = code.InteractiveConsole(vars)
    shell.interact()

msg("Hi, reading yy_df.")
yy_df = read_pickle(sys.argv[1])

msg("Standardizing all with standardscaler")
scaler = StandardScaler()
yycols = list(yy_df.columns)
yycols.remove('elo')
yycols.remove('opening_feature')
toscale = yy_df[yycols]
scaled = scaler.fit_transform(toscale)
yy_df[yycols] = scaled

msg("Writing yy_df back out, standardized")
yy_df.to_pickle(sys.argv[1])
