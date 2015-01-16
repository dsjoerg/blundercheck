#!/usr/bin/env python

import boto.sqs
import sys
import argparse
import time

parser = argparse.ArgumentParser(description='Peek at an SQS queue')
parser.add_argument('queuename', metavar='queuename',
                   help='name of the SQS queue')
parser.add_argument('--show-messages', dest='showmessages', action='store_true')
parser.add_argument('--no-show-messages', dest='showmessages', action='store_false')
parser.set_defaults(showmessages=False)
args = parser.parse_args()

conn = boto.sqs.connect_to_region("us-east-1")
q = conn.get_queue(args.queuename)
print("%s ITEMS IN QUEUE at %s" % (q.count(), time.strftime('%Y%m%d-%H%M%S')))

if q.count() > 0:
    if args.showmessages:
        l = q.get_messages(10, 10)
        while l:
            for m in l:
                b = m.get_body()
#                print("LEN: %i" % len(b))
#                print(b.encode('ascii', 'ignore'))
                print("MESSAGE: %s" % b)
            l = q.get_messages(10, 10)

    #    m = q.read()
    #    while m is not None:
    #        m = q.read()
    else:
        m = q.read()
        print("FIRST MESSAGE: %s" % m.get_body())

