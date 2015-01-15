#!/usr/bin/env python

import tutum, sys, time

nodes = tutum.Node.list()
for node in nodes:
  print 'node %s, state %s' % (node.uuid, node.state)
  if node.state != 'Terminated':
    node.delete()
