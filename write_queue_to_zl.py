#!/usr/bin/env python

import boto.sqs
import sys, argparse, zlib

parser = argparse.ArgumentParser(description='Write an SQS queue to stdout as a zlib')
parser.add_argument('queuename', metavar='queuename',
                   help='name of the SQS queue')
args = parser.parse_args()

conn = boto.sqs.connect_to_region("us-east-1")
q = conn.get_queue(args.queuename)

ms = []
msgnumber = 0
while True:
    nextmsg = q.read()
    if nextmsg is None:
        break
    ms.append(nextmsg)
    msgnumber = msgnumber + 1
    if msgnumber % 10 == 0:
        sys.stderr.write('.'),
        sys.stderr.flush()

blob = "["
for m in ms:
    blob += m.get_body() + ","
blob += "]"

print zlib.compress(blob)

# clear the messages from the outqueue
for m in ms:
    m.delete()
