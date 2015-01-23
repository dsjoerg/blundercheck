#!/usr/bin/env python

import tutum
import time, sys

servicenum = sys.argv[1]
MAX_CONTAINERS_PER_SERVICE = 10

def msg(str):
    print "%s %s" % (time.strftime('%Y%m%d-%H%M%S'), str)
    sys.stdout.flush()

envvars = {'MOVETIME': 2000,
           'THREADS': 1,
           'HASH': 1000}

msg("Launching 10 scorecontainers")
servicename = "scorecontainer%s" % servicenum
service = tutum.Service.create(image="tutum.co/dsjoerg/fun", name=servicename, target_num_containers=MAX_CONTAINERS_PER_SERVICE, container_envvars=envvars)
service.save()
service.start()
msg("Done. Service uuid = %s" % service.uuid)
