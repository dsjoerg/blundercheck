#!/usr/bin/env python

import tutum
import time, sys
from djeval import *

SCORESERVERS_PER_CONTAINER = 32

envvars = []
envvars.append({"key": "NUM_SCORESERVERS", "value": str(SCORESERVERS_PER_CONTAINER)})
envvars.append({"key": "MOVETIME", "value": "2000"})
envvars.append({"key": "THREADS", "value": "1"})
envvars.append({"key": "HASH", "value": "1000"})

msg("Launching all scorecontainers")
servicename = "scorecontainer%s%s" % (servicenum, time.strftime('%Y%m%d-%H%M%S'))
service = tutum.Service.create(image="tutum.co/dsjoerg/kaggle-chess", name=servicename, container_envvars=envvars, deployment_strategy='EVERY_NODE', tags=[{'name': 'scorecontainer'}])

service.save()
service.start()
msg("Done. Service uuid = %s" % service.uuid)
