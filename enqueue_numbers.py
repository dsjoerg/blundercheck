#!/usr/bin/env python

import boto.sqs
import sys


conn = boto.sqs.connect_to_region("us-east-1")
q = conn.get_queue('numbers')

batch = []
for game_num in range(1,50001):

#    m = boto.sqs.message.Message()
#    m.set_body(str(game_num))
    batch.append((game_num, str(game_num), 0))
    if len(batch) == 10:
        q.write_batch(batch)
        batch = []
    if game_num % 100 == 0:
        print '.',
        sys.stdout.flush()
