#!/usr/bin/env python

import sys, os, json, zlib, string, gzip

outfd = gzip.open(sys.argv[-1], 'wb')
i = 0
for garchive in sys.argv[1:-1]:
        infd = gzip.open(garchive, 'rb')
        for line in infd:
                outfd.write(line)
                if i % 500 == 0:
                        sys.stdout.write('.')
                        sys.stdout.flush()
                i = i + 1
        infd.close()
outfd.close()
