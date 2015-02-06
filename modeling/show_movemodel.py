#!/usr/bin/env python

import sys
import pygraphviz as pgv
from StringIO import StringIO
from pandas import DataFrame
from sklearn.externals import joblib
from sklearn import tree

rfr, features_to_use = joblib.load(sys.argv[1])

print "Feature importances:"
print DataFrame([rfr.feature_importances_, features_to_use]).transpose().sort([0], ascending=False)

print "There are %i estimators. Here is the first one:" % len(rfr.estimators_)

dot_data = StringIO()
tree.export_graphviz(rfr.estimators_[0], out_file=dot_data, feature_names=features_to_use)
print dot_data.getvalue()

B=pgv.AGraph(dot_data.getvalue())
B.layout('dot')
B.draw('/data/rfr.png') # draw png

print "Wrote that estimator to /data/rfr.png"
