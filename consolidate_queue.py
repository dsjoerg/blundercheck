#!/usr/bin/env python

import sys, argparse, time, random, string
import boto.sqs
from boto.s3.key import Key
from djeval import *


# read N json items in from a given queue, and write them to a given 

parser = argparse.ArgumentParser(description='Read N items from an SQS queue and write them to a bucket')
parser.add_argument('queue', help='name of the SQS queue to read from')
parser.add_argument('num_items', help='number of items to read')
parser.add_argument('bucket', help='name of the S3 bucket to write to')
parser.add_argument('keyfolder', help='name of the S3 keyfolder (prefix) to use')
args = parser.parse_args()

conn = boto.sqs.connect_to_region("us-east-1")
q = conn.get_queue(args.queue)
msg("%s ITEMS IN QUEUE." % q.count())

ms = []
msg("READING %i ITEMS." % int(args.num_items))
for ix in range(0, int(args.num_items)):
    nextmsg = q.read()
    if nextmsg is None:
        break
    ms.append(nextmsg)

msg("COMPOSING BIG BLOB.")
blob = "["
for m in ms:
    blob = blob + m.get_body() + ", "
blob = blob + "]"

random.seed()
fifty = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(50))
keyname = '%s/%s.json' % (args.keyfolder, fifty)
msg("WRITING ITEMS TO BUCKET %s, KEY %s" % (args.bucket, keyname))
s3conn = boto.connect_s3()
bucket = s3conn.get_bucket(args.bucket)
k = Key(bucket)
k.key = keyname
k.set_contents_from_string(blob)

msg("DELETING ITEMS FROM QUEUE")
for m in ms:
    m.delete()

msg("DONE")
