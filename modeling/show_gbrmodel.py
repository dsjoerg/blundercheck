#!/usr/bin/env python

import matplotlib
matplotlib.use('Agg') # Must be before importing matplotlib.pyplot or pylab!

import sys
import pygraphviz as pgv
from StringIO import StringIO
from pandas import DataFrame
from sklearn.externals import joblib
from sklearn import tree
import matplotlib.pyplot as plt

gbr, features = joblib.load(sys.argv[1])

print "Train score:"
print gbr.train_score_

print "Feature importances:"
print DataFrame([gbr.feature_importances_, features]).transpose().sort([0], ascending=False)

print "There are %i estimators. Here is the first one:" % len(gbr.estimators_)

print gbr.estimators_[0][0].tree_

dot_data = StringIO()
tree.export_graphviz(gbr.estimators_[0][0], out_file=dot_data, feature_names=features)
print dot_data.getvalue()

B=pgv.AGraph(dot_data.getvalue())
B.layout('dot')
B.draw('/data/gbr.png') # draw png

print "Wrote that estimator to /data/gbr.png"
