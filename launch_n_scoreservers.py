#!/usr/bin/env python

import sys, subprocess, argparse

parser = argparse.ArgumentParser(description='Launch n scoreserver to score games')
parser.add_argument('num_nodes', metavar='num_nodes', type=int,
                   help='number of actual machines to launch')
parser.add_argument('-t', dest='tag', metavar='tag', help='tag to use on this cluster', required=True)
args = parser.parse_args()
tag = args.tag
num_nodes = args.num_nodes

for i in range(0, num_nodes / 10):
    subprocess.Popen(["./launch_scoreservers.py", "-f", "10", "-t", tag])
