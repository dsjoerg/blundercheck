#!/usr/bin/env python

import sys, os, json, zlib, string, gzip

# thanks to http://stackoverflow.com/questions/20449625/python-compressing-a-series-of-json-objects-while-maintaining-serial-reading

LOW_GAMENUM=int(sys.argv[2])
HIGH_GAMENUM=int(sys.argv[3])

expected_gamenums = set(range(LOW_GAMENUM, HIGH_GAMENUM+1))

i = 0
for fname in os.listdir(sys.argv[1]):
        sys.stdout.flush()
        fd = open(sys.argv[1] + '/' + fname, 'r')
        thestr = zlib.decompress(fd.read())
        thestr = string.replace(thestr, '}, ]', '} ]')
        thestr = string.replace(thestr, '},]', '} ]')
        theitems = json.loads(thestr)
        for item in theitems:
                if (int(item['event']) >= LOW_GAMENUM) and (int(item['event']) <= HIGH_GAMENUM):
                        expected_gamenums.discard(int(item['event']))
        if i % 50 == 0:
                sys.stdout.write('.')
                sys.stdout.flush()
        i = i + 1

print "There were %i files" % (i)
print "The following %i expected gamenums were not found: [" % len(expected_gamenums)
for num in expected_gamenums:
        print "%i," % num
print "]"

