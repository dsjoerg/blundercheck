#!/usr/bin/env python

import tutum, sys, time

nodeclusters = tutum.NodeCluster.list()
for nc in nodeclusters:
  print 'cluster %s, state %s' % (nc.uuid, nc.state)
  if nc.state not in ['Terminated', 'Terminating']:
    nc.delete()
