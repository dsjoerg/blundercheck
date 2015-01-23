#!/usr/bin/env python

import tutum
import time, sys

servicenum = sys.argv[1]
MAX_CONTAINERS_PER_SERVICE = 10
SCORESERVERS_PER_CONTAINER = 32

def msg(str):
    print "%s %s" % (time.strftime('%Y%m%d-%H%M%S'), str)
    sys.stdout.flush()

envvars = []
envvars.append({"key": "NUM_SCORESERVERS", "value": str(SCORESERVERS_PER_CONTAINER)})
envvars.append({"key": "MOVETIME", "value": "2000"})
envvars.append({"key": "THREADS", "value": "1"})
envvars.append({"key": "HASH", "value": "1000"})

msg("Launching 10 scorecontainers, each with %i scoreservers" % SCORESERVERS_PER_CONTAINER)
servicename = "scorecontainer%s%s" % (servicenum, time.strftime('%Y%m%d-%H%M%S'))
service = tutum.Service.create(image="tutum.co/dsjoerg/fun", name=servicename, target_num_containers=MAX_CONTAINERS_PER_SERVICE, container_envvars=envvars)
service.save()
service.start()
msg("Done. Service uuid = %s" % service.uuid)
