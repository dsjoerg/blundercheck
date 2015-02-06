#!/usr/bin/env python

import sys, os, json, zlib, string

all_items = []

i = 0
for fname in os.listdir('.'):
        fd = open(fname, 'r')
        thestr = zlib.decompress(fd.read())
        thestr = string.replace(thestr, '}, ]', '} ]')
        theitems = json.loads(thestr)
        all_items.extend(theitems)
        if i % 10 == 0:
                sys.stdout.write('.')
                sys.stdout.flush()
        i = i + 1

print "There were %i items in %i files" % (len(all_items), i)

bigstr = json.dumps(all_items)
bigzl = zlib.compress(bigstr)
outfd = open('../big.json.zl', 'wb')
outfd.write(bigzl)
