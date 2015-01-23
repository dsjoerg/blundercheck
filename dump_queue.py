#!/usr/bin/env python

import boto.sqs
import sys
import argparse

parser = argparse.ArgumentParser(description='Clear out an SQS queue')
parser.add_argument('queuename', metavar='queuename',
                   help='name of the SQS queue')
parser.add_argument('--show-messages', dest='showmessages', action='store_true')
parser.add_argument('--no-show-messages', dest='showmessages', action='store_false')
parser.set_defaults(showmessages=False)
args = parser.parse_args()

conn = boto.sqs.connect_to_region("us-east-1")
q = conn.get_queue(args.queuename)
print("%s ITEMS IN QUEUE." % q.count())

if args.showmessages:
    m = q.read(300)
    while m is not None:
        print("MESSAGE: %s" % m.get_body())
        m = q.read(300)

q.purge()

print "QUEUE EMPTY NOW"
