#!/usr/bin/env python

import sys, os, json, zlib, string, gzip

# thanks to http://stackoverflow.com/questions/20449625/python-compressing-a-series-of-json-objects-while-maintaining-serial-reading

outfd = gzip.open('../big.json.gz', 'wb')

i = 0
for fname in os.listdir('.'):
        fd = open(fname, 'r')
        thestr = zlib.decompress(fd.read())
        thestr = string.replace(thestr, '}, ]', '} ]')
        theitems = json.loads(thestr)
        for item in theitems:
                outfd.write(json.dumps(item) + '\n')
        if i % 50 == 0:
                sys.stdout.write('.')
                sys.stdout.flush()
        i = i + 1

outfd.close()

print "There were %i files" % (i)

