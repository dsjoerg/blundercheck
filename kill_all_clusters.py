#!/usr/bin/env python

import tutum, sys, time

print 'killing clusters'
nodeclusters = tutum.NodeCluster.list()
for nc in nodeclusters:
  print 'cluster %s, state %s' % (nc.uuid, nc.state)
  if nc.state not in ['Terminated', 'Terminating']:
    nc.delete()

print 'killing services'
for service in tutum.Service.list():
  if service.state not in ['Starting', 'Terminated']:
    print 'killing service %s, %s' % (service.uuid, service.name)
    service.delete()
