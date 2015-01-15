#!/usr/bin/env python

import boto.sqs
import sys

queuename = sys.argv[1]

conn = boto.sqs.connect_to_region("us-east-1")
q = conn.get_queue(queuename)
m = q.read()
while m is not None:
    print("MESSAGE: %s" % m.get_body())
    q.delete_message(m)
    m = q.read()

print "QUEUE EMPTY NOW"
