#!/usr/bin/env python

import boto.sqs
from boto.sqs.message import Message
import sys


conn = boto.sqs.connect_to_region("us-east-1")
q = conn.get_queue('numbers')
m = boto.sqs.message.Message()

batch = []
for game_num in range(1,50001):

    m.set_body(str(game_num))
    batch.append((game_num, m.get_body_encoded(), 0))
    if len(batch) == 10:
        q.write_batch(batch)
        batch = []
    if game_num % 100 == 0:
        print '.',
        sys.stdout.flush()
