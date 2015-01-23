#!/usr/bin/env python

import tutum, sys, time, argparse

parser = argparse.ArgumentParser(description='Kill clusters and services as requested')
parser.add_argument('-c', dest='kill_clusters', action='store_true', help='kill clusters')
parser.add_argument('-s', dest='kill_services', action='store_true', help='kill services')
parser.set_defaults(kill_clusters=False, kill_services=False)
args = parser.parse_args()

if args.kill_clusters:
  print 'killing clusters'
  nodeclusters = tutum.NodeCluster.list()
  for nc in nodeclusters:
    print 'cluster %s, state %s' % (nc.uuid, nc.state)
    if nc.state not in ['Terminated', 'Terminating']:
      nc.delete()

if args.kill_services:
  print 'killing services'
  for service in tutum.Service.list():
    if service.state not in ['Starting', 'Terminated', 'Terminating', 'Init']:
      print 'killing service %s "%s" (%s)' % (service.uuid, service.name, service.state)
      service.delete()
    else:
      print 'not killing service %s "%s" (%s)' % (service.uuid, service.name, service.state)
