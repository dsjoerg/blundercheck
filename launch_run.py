#!/usr/bin/env python

import tutum, sys

job_name = sys.argv[1]

tutum.user = "dsjoerg"
tutum.apikey = sys.argv[2]

# waiting for https://github.com/tutumcloud/api-docs/issues/17
#
#region = tutum.Region.fetch("aws/us-east-1")
#node_type = tutum.NodeType.fetch("aws/t2.micro")
#nodecluster = tutum.NodeCluster.create(name="this", node_type=node_type, region=region)

# TODO create cluster when launching jobs, and somehow automatically
# kill cluster when jobs are complete?
if False:
    nodecluster = tutum.NodeCluster.create(name="this", node_type='/api/v1/nodetype/aws/t2.micro/', region='/api/v1/region/aws/us-east-1/', target_num_nodes=5)
    nodecluster.save()
    nodecluster.deploy()

for job_num in range(0, 5):
    print "Launching job %d" % job_num
    envvars = []
    envvars.append({"key": "CONFIG_BUCKET", "value": "bc-runconfigs"})
    config_key = '%s/%d.json' % (job_name, job_num)
    envvars.append({"key": "CONFIG_KEY", "value": config_key})
    service = tutum.Service.create(image="tutum.co/dsjoerg/fun", name="thing", target_num_containers=1, container_envvars=envvars)
    service.save()
    service.start()
