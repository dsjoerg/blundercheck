#!/usr/bin/env python

import sys, subprocess

for i in range(0,int(sys.argv[1]) / 10):
    subprocess.Popen(["./launch_scoreservers.py", "-f", "10"])
