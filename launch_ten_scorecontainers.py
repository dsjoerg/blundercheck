#!/usr/bin/env python

import tutum
import time, sys

MAX_CONTAINERS_PER_SERVICE = 10

def msg(str):
    print "%s %s" % (time.strftime('%Y%m%d-%H%M%S'), str)
    sys.stdout.flush()

msg("Launching 10 scorecontainers")
service = tutum.Service.create(image="tutum.co/dsjoerg/fun", target_num_containers=MAX_CONTAINERS_PER_SERVICE)
service.save()
service.start()
msg("Done. Service uuid = %s" % service.uuid)
