#!/usr/bin/env python

import tutum, sys, time, subprocess

CONTAINERS_PER_NODE = 32
MAX_CONTAINERS_PER_SERVICE = 10

num_nodes = int(sys.argv[1])

tutum.user = "dsjoerg"
tutum.apikey = sys.argv[2]

# waiting for https://github.com/tutumcloud/api-docs/issues/17
#
#region = tutum.Region.fetch("aws/us-east-1")
#node_type = tutum.NodeType.fetch("aws/t2.micro")
#nodecluster = tutum.NodeCluster.create(name="this", node_type=node_type, region=region)

def msg(str):
    print "%s %s" % (time.strftime('%Y%m%d-%H%M%S'), str)

nodecluster = None

nodeclusters = tutum.NodeCluster.list()
nodeclusters = [nc for nc in nodeclusters if nc.state not in ['Terminating', 'Terminated']]
if len(nodeclusters) == 0:
    msg("Launching cluster")
    nodecluster = tutum.NodeCluster.create(name="scoreservers", node_type='/api/v1/nodetype/aws/c3.8xlarge/', region='/api/v1/region/aws/us-east-1/', target_num_nodes=num_nodes)
    nodecluster.save()
else:
    nodecluster = nodeclusters[0]

msg("Using nodecluster %s, current state %s" % (nodecluster.uuid, nodecluster.state) )

if nodecluster.state == 'Init':
    nodecluster.deploy()
    # is this next line needed or does deploy() do it for us?
    nodecluster.state = 'Deploying'

if nodecluster.state == 'Deploying':
    while tutum.NodeCluster.fetch(nodecluster.uuid).state != 'Deployed':
        msg("Waiting for cluster %s to come up. State=%s, current_num_nodes=%s" % (nodecluster.uuid, nodecluster.state, nodecluster.current_num_nodes))
        time.sleep(5)

num_containers = num_nodes * CONTAINERS_PER_NODE
num_services = num_containers / MAX_CONTAINERS_PER_SERVICE


services = []
for service_num in range(0, num_services):
    msg("Launching service %d" % service_num)
    subprocess.Popen(["./launch_ten_scorecontainers.py", str(service_num)])
    if False:
        service = tutum.Service.create(image="tutum.co/dsjoerg/fun", name="scorecontainer", target_num_containers=MAX_CONTAINERS_PER_SERVICE)
        service.save()
        service.start()
        services.append(service)

if False:
    while True:
        statuses = set([tutum.Service.fetch(service.uuid).state for service in services])
        msg("Statuses are %s" % statuses)
        time.sleep(5)
        if 'Starting' not in statuses:
            break

print "Containers are up, services are launching.  Don't forget to kill someday."
