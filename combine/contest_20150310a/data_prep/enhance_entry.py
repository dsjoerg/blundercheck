#!/usr/bin/env python

import sys, csv

elos = {}
with open(sys.argv[1], 'r') as k25_file:
     reader = csv.reader(k25_file, delimiter=',')
     for row in reader:
          elos[row[0]] = [row[1], row[2]]

with open(sys.argv[2], 'r') as certain_elo_file:
     reader = csv.reader(certain_elo_file, delimiter=',')
     for row in reader:
          elos[row[0]] = elos[row[1]]
         
with open(sys.argv[3], 'r') as prediction_file:
     reader = csv.reader(prediction_file, delimiter=',')
     for row in reader:
          if row[0] in elos:
               print '%s,%s,%s' % (row[0], elos[row[0]][0], elos[row[0]][1])
          else:
               print '%s,%s,%s' % (row[0], row[1], row[2])
