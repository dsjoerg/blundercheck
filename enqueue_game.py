#!/usr/bin/env python

import boto.sqs
import sys

pgn_string = sys.stdin.read(1000000)

conn = boto.sqs.connect_to_region("us-east-1")
q = conn.get_queue('games')
m = boto.sqs.message.Message()
m.set_body(pgn_string)
q.write(m)
