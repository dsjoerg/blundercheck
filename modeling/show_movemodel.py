#!/usr/bin/env python

import sys
import pydot
from StringIO import StringIO
from sklearn.externals import joblib
from sklearn import tree

rfr = joblib.load(sys.argv[1])

tree.export_graphviz(rfr.estimators_[0], out_file='/data/rfr.dot')

dot_data = StringIO()
tree.export_graphviz(rfr.estimators_[0], out_file=dot_data)
print dot_data.getvalue()
pydot.graph_from_dot_data(dot_data.getvalue()).write_pdf('/data/rfr.pdf') 
