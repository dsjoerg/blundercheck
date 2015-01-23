#!/usr/bin/env python

import boto.sqs
import sys
import argparse

parser = argparse.ArgumentParser(description='Write an SQS queue to stdout')
parser.add_argument('queuename', metavar='queuename',
                   help='name of the SQS queue')
args = parser.parse_args()

conn = boto.sqs.connect_to_region("us-east-1")
q = conn.get_queue(args.queuename)

print "["

m = q.read()
while m is not None:
    print(m.get_body())
    m = q.read()
    print(",")
    sys.stdout.flush()
    m.delete()

print "]"
