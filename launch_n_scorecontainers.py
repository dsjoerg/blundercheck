#!/usr/bin/env python

import sys, subprocess

for i in range(0,int(sys.argv[1])):
    subprocess.Popen(["./launch_ten_scorecontainers.py", str(i)])
