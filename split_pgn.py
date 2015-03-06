#!/usr/bin/env python

import sys, os

# take a PGN from stdin, write it out to a directory named the same as the file with .dir
infilename = sys.argv[1]
num_per_file = int(sys.argv[2])
outdir = infilename + '.dir'
infile = open(infilename, 'r')

if not os.path.exists(outdir):
    os.makedirs(outdir)

outfilenum = 0
num_in_outfile = 0
outfile = open(outdir + '/' + str(outfilenum) + '.pgn', 'w')

def dump(pgn_string):
    global outfilenum
    global num_in_outfile
    global outfile

    outfile.write(pgn_string)
    num_in_outfile = num_in_outfile + 1
    if num_in_outfile > num_per_file:
        outfile.close()
        outfilenum = outfilenum + 1
        outfile = open(outdir + '/' + str(outfilenum) + '.pgn', 'w')
        num_in_outfile = 0
        sys.stderr.write('Wrote out file %i\n' % outfilenum)

# read in a PGN into memory
pgn = ""
read_any = False
for line in infile:
    line = line.strip()
    if line[0:6] == '[Event':
        if read_any:
            dump(pgn)
        read_any = True
        pgn = ""
    pgn = pgn + line + '\n'

dump(pgn)
outfile.close()
