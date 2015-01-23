
import chess.pgn
import chess
import pystockfish
import os
import boto
import boto.sqs
from boto.sqs.message import Message
import time
import json
import StringIO
import subprocess
from djeval import *

num_scoreservers = int(os.environ['NUM_SCORESERVERS'])

msg("Hi! Launching %i scoreservers." % (num_scoreservers))

for i in range(0,num_scoreservers):
    subprocess.Popen(["python", "/root/src/blundercheck/scoreserver.py"])

msg("Launched!")

while True:
    time.sleep(100)
