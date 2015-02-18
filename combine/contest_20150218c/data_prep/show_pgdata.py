#!/usr/bin/env python

from pandas  import *
import numpy as np
from djeval import *

msg("Hi, reading yy_df.")
yy_df = read_pickle(sys.argv[1])

# warn about bad data counts

counts = yy_df.count(axis=0)
cols_bad = (counts % 50000 != 0)
num_bad_columns = len(counts[cols_bad])
if num_bad_columns > 0:
    msg("WARNING there are %i bad columns." % num_bad_columns)
    msg("They are:")
    msg(counts[cols_bad])

for colname in yy_df.columns.values:
    if np.sum(notnull(yy_df[colname])) % 50000 != 0:
        print '%s has only %i notnull values' % (colname, np.sum(notnull(yy_df[colname])))
#    msg('Looking at %s' % colname)
    if yy_df[colname].dtype != 'float32':
        if np.sum(np.isfinite(yy_df['meanecho'])) % 50000 != 0:
            print '%s has only %i finite values' % (colname, np.sum(np.isfinite(yy_df['meanecho'])))
    else:
        X = np.asanyarray(yy_df[colname])
        if (X.dtype.char in np.typecodes['AllFloat'] and not np.isfinite(X.sum())
                and not np.isfinite(X).all()):
            msg('OOOPPPS Problem with %s' % colname)
            raise ValueError('PROBLEM VAR')
