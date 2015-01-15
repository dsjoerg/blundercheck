#!/usr/bin/env python

import tutum, sys, time

job_name = sys.argv[1]
num_nodes = int(sys.argv[2])

tutum.user = "dsjoerg"
tutum.apikey = sys.argv[3]

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
    nodecluster = tutum.NodeCluster.create(name="this", node_type='/api/v1/nodetype/aws/t2.micro/', region='/api/v1/region/aws/us-east-1/', target_num_nodes=num_nodes)
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
        
services = []
for job_num in range(0, num_nodes):
    msg("Launching job %d" % job_num)
    service = tutum.Service.create(image="tutum.co/dsjoerg/fun", target_num_containers=1)
    service.save()
    service.start()
    services.append(service)

while True:
    statuses = set([tutum.Service.fetch(service.uuid).state for service in services])
    msg("Statuses are %s" % statuses)
    time.sleep(5)
    if 'Running' not in statuses and 'Starting' not in statuses:
        break

msg("Deleting cluster %s" % nodecluster.uuid)
nodecluster.delete()
