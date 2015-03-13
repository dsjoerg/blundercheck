#!/bin/bash

THING=$1

aws s3 sync s3://bc-runoutputs/$THING /tmp/$THING
consolidate_zls_to_gz.py /tmp/$THING 1 50000 /tmp/$THING.gz
aws s3 cp /tmp/$THING.gz s3://bc-runoutputs/$THING.gz --acl public-read
