#!/usr/bin/env python

import tutum
import time, sys, argparse

parser = argparse.ArgumentParser(description='Launch scorecontainers on all the nodes having the given tag')
parser.add_argument('-t', dest='tag', metavar='tag', help='tag indicated which nodes to launch on', required=True)
args = parser.parse_args()

def msg(str):
    print "%s %s" % (time.strftime('%Y%m%d-%H%M%S'), str)

SCORESERVERS_PER_CONTAINER = 32

envvars = []
envvars.append({"key": "NUM_SCORESERVERS", "value": str(SCORESERVERS_PER_CONTAINER)})
envvars.append({"key": "DEBUG", "value": "1"})
envvars.append({"key": "MIN_ITEMS_PER_KEY", "value": "200000"})
envvars.append({"key": "MOVETIME", "value": "16000"})
envvars.append({"key": "THREADS", "value": "1"})
envvars.append({"key": "HASH", "value": "1000"})

msg("Launching all scorecontainers on tag %s" % args.tag)
servicename = "scorecontainer%s" % (time.strftime('%Y%m%d-%H%M%S'))
service = tutum.Service.create(image="tutum.co/dsjoerg/scoreserver", name=servicename, container_envvars=envvars, deployment_strategy='EVERY_NODE', tags=[{'name': args.tag}])

service.save()
service.start()
msg("Done. Service uuid = %s" % service.uuid)
