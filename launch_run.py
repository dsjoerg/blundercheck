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

msg("Launching cluster")
nodecluster = tutum.NodeCluster.create(name="this", node_type='/api/v1/nodetype/aws/t2.micro/', region='/api/v1/region/aws/us-east-1/', target_num_nodes=num_nodes)
nodecluster.save()
nodecluster.deploy()
while tutum.NodeCluster.fetch(nodecluster.uuid).state != 'Deployed':
    msg("Waiting for cluster to come up...")
    time.sleep(5)
        
services = []
for job_num in range(0, num_nodes):
    msg("Launching job %d" % job_num)
    envvars = []
    envvars.append({"key": "CONFIG_BUCKET", "value": "bc-runconfigs"})
    config_key = '%s/%d.json' % (job_name, job_num)
    envvars.append({"key": "CONFIG_KEY", "value": config_key})
    service = tutum.Service.create(image="tutum.co/dsjoerg/fun", name="thing", target_num_containers=1, container_envvars=envvars)
    service.save()
    service.start()
    services.append(service)

while True:
    statuses = set([tutum.Service.fetch(service.uuid).state for service in services])
    msg("Statuses are %s" % statuses)
    time.sleep(5)
    if 'Running' not in statuses and 'Starting' not in statuses:
        break

msg("Deleting cluster")
nodecluster.delete()
