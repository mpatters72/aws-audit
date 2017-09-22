#!/usr/bin/env python
import botocore
import boto3
import re
import argparse
import logging
from botocore.client import Config

# This script is designed to add tags to s3 buckets matching naming conventions
# Because bucket_tagging.put overrides all existing tags, it checks for old ones and combines tags before putting
# If you just want to audit, set addtags to 'no'
# ./s3Tag.py --pattern [matchingstring in bucketname] --addtags <yes|no> --tagkey <keyname> --tagvalue <keyvalue>

# attempts to put policies on a bucket and test result
parser = argparse.ArgumentParser()
parser.add_argument('-l', '--log', default='CRITICAL', help='loglevel, eg DEBUG, INFO, WARNING, ERROR, CRITICAL')
parser.add_argument('-p', '--pattern', default='mikepatterson', help='pattern in bucket name, eg static')
parser.add_argument('-a', '--addtags', default='no', help='add/update tags on bucket yes or no')
parser.add_argument('-k', '--tagkey', default='', help='key for tag e.g. \"Adobe:DataClassification\"')
parser.add_argument('-v', '--tagvalue', default='', help='value for tag e.g. \"Private\"')

# convert lower to upper case if passed
def initLogging(loglevel):
    numeric_level = getattr(logging, loglevel.upper(), 'WARNING')
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    logging.basicConfig(level=numeric_level)

#return list of buckets matching string
def findBuckets(resource, pattern):
    if not pattern:
        exit('pattern can not be empty')
    buckets=[]
    for bucket in resource.buckets.all():
        logging.debug("bucket found: %s" , bucket.name)
        if pattern in str(bucket.name):
            logging.warn("bucket matching: %s pattern: %s", bucket.name, pattern)
            buckets.append(bucket.name)
    return buckets

# return existing tags if there are any
def getOldTags(client, bucket):
    old_tags = []
    try:
        tags = client.get_bucket_tagging(Bucket=bucket)
        if tags:
            old_tags = old_tags + tags['TagSet']
    except:
        logging.warn("No tags on bucket: " + bucket)
    logging.warn("old_tags: " + str(old_tags) )
    return old_tags

def printTags(client, buckets):
    if not buckets:
         exit('No buckets found')
    for bucket in buckets:
        logging.warn("bucket: " + str(bucket) )
        old_tags = getOldTags(client, str(bucket))
        logging.warn("old_tags: " + str(old_tags) )
        if old_tags:
            for tag in old_tags:
                print bucket + " " + str(tag['Key']) + " " + str(tag['Value'])
        else: 
            print str(bucket) + " NO TAGS"

# put tags on buckets, unless it already has tags starting with 'aws:' since we cannot reapply those
def putTag(client, resource, buckets, key, value):
    new_tags = [{'Key': key, 'Value': value}]
    if key is '' or value is '':
        print "Can't update with blank tag key or value"
        exit(1)
    for bucket in buckets:
        aws_tagged = False
        combined_tags = list(new_tags)
        old_tags = getOldTags(client, bucket)
        logging.warn("old_tags: " + str(old_tags) )
        for tag in old_tags:
            if tag['Key'] != key:
                combined_tags.append({'Key': tag['Key'], 'Value': tag['Value']})
            if 'aws' in tag['Key']:
                aws_tagged = True
        logging.warn("Updating tags on bucket: %s", bucket)
        bucket_tagging = resource.BucketTagging(bucket)
        if aws_tagged is False:
            puttag_result = bucket_tagging.put( Tagging={ 'TagSet': combined_tags } )
            logging.debug(puttag_result)
        else:
            print "WARN: cannot apply tags on " + bucket

def main ():
    args = parser.parse_args()
    pattern = args.pattern
    addtags = args.addtags
    tagkey = args.tagkey
    tagvalue = args.tagvalue
    loglevel = args.log
    initLogging(loglevel)
    client=boto3.client('s3', config=Config(signature_version='s3v4'))
    resource = boto3.resource('s3', config=Config(signature_version='s3v4'))
    matching_buckets = findBuckets(resource, pattern)
    printTags(client, matching_buckets)
    if addtags in ['yes','y','Yes','YES']:
        print "Planning to add/update this tag: " + tagkey + " value: " + tagvalue + " to the matching buckets shown" 
        putTag(client, resource, matching_buckets, tagkey, tagvalue)
        print "########## status after update ##########"
        printTags(client, matching_buckets)
    
if __name__ == '__main__':
    main()
