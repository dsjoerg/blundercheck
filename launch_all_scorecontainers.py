#!/usr/bin/env python

import tutum
import time, sys

def msg(str):
    print "%s %s" % (time.strftime('%Y%m%d-%H%M%S'), str)

SCORESERVERS_PER_CONTAINER = 36

envvars = []
envvars.append({"key": "NUM_SCORESERVERS", "value": str(SCORESERVERS_PER_CONTAINER)})
envvars.append({"key": "MOVETIME", "value": "2000"})
envvars.append({"key": "THREADS", "value": "1"})
envvars.append({"key": "HASH", "value": "1000"})

msg("Launching all scorecontainers")
servicename = "scorecontainer%s" % (time.strftime('%Y%m%d-%H%M%S'))
service = tutum.Service.create(image="tutum.co/dsjoerg/scoreserver", name=servicename, container_envvars=envvars, deployment_strategy='EVERY_NODE', tags=[{'name': 'scorecontainer'}])

service.save()
service.start()
msg("Done. Service uuid = %s" % service.uuid)
