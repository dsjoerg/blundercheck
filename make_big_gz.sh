#!/bin/bash

aws s3 sync s3://bc-runoutputs/20150312 /tmp/20150312
consolidate_zls_to_gz.py /tmp/20150312 1 50000 /tmp/20150312.gz
aws s3 cp /tmp/20150312.gz s3://bc-runoutputs/20150312.gz --acl public-read
