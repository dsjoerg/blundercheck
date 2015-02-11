#!/usr/bin/env python

import sys
import pygraphviz as pgv
from StringIO import StringIO
from pandas import DataFrame
from sklearn.externals import joblib
from sklearn import tree

gbr, features = joblib.load(sys.argv[1])

print "Feature importances:"
print DataFrame([gbr.feature_importances_, features]).transpose().sort([0], ascending=False)

print "There are %i estimators. Here is the first one:" % len(gbr.estimators_)

print gbr.estimators_[0]
