#!/usr/bin/env python
import botocore
import boto3
import re
import argparse
import logging
from botocore.client import Config

# This script enables s3 bucket versioning and sets a LifeCycle policy to remove old versions after X days
# Some AWS regions e.g. eu-central-1 need different parameters for s3v4, option to override that
# When applying LifeCycle policies it's dangeorus as it is an all or nothing override, so there is a failsafe to not apply policy if other ones already exist

# attempts to put policies on a bucket and test result
parser = argparse.ArgumentParser()
parser.add_argument('-l', '--log', default='WARNING', help='loglevel, eg DEBUG, INFO, WARNING, ERROR, CRITICAL')
parser.add_argument('--bucket', default='adobespark-dev-mpatters')
parser.add_argument('--days', default=90)

# convert lower to upper case if passed
def initLogging(loglevel):
    numeric_level = getattr(logging, loglevel.upper(), 'WARNING')
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    logging.basicConfig(level=numeric_level)

def bucketVersioning(s3resource,bucket,action):
    s3 = s3resource
    bucket_versioning = s3.BucketVersioning(bucket)
    if action=='status':
        bucket_versioning.load()
        return "Bucket versioning status: %s", bucket_versioning.status
    elif action=='enable':
       bucket_versioning.enable(bucket)
       logging.info("Versioning is enabled on %s", bucket)
       return 0
    elif action=='disable':
       bucket_versioning.disable(bucket)
       return 0
    else:
        logging.error("No match on %s", bucket)
        return 0
        
    
# count existing rules on bucket prior to making changes
def bucketPolicyRuleCount(bucket,s3conn):
    logging.debug("bucket: %s, s3conn: %s", bucket, s3conn)
    bucket_lifecycle = s3conn.BucketLifecycle(bucket)
    try:
        bucket_lifecycle.load()
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchLifecycleConfiguration':
            logging.debug("Rule length: 0")
            return 0
        elif e.response['Error']['Code'] == 'PermanentRedirect':
            logging.warn("PermanentRedirect, not a blocker, but investigate this bucket offline - may be a duplicte bucket: %s", bucket)
            return 0
        else:
            raise Exception("Unexpected error: %s" % e)
            
    bucket_lifecycle.load()
    rules = bucket_lifecycle.rules
    logging.debug("Rules: %s", str(rules))
    logging.debug("Rule length: %s", str(len(rules)))
    return len(rules)

def versionExpirePolicy(s3client, s3conn, bucket, days):
    if bucketPolicyRuleCount(bucket,s3conn) > 0:
        logging.error("There are already LifeCycle policies on this bucket, too dangerous, exiting, manual review needed on: %s", bucket)
        return False
    expireVersionDays =  { 'ID':'expireVersionedWholeBucket', 'Prefix':'', 'Status':'Enabled', 'NoncurrentVersionExpiration': { 'NoncurrentDays': days }, 'Expiration': { 'ExpiredObjectDeleteMarker': True }}
    rules = [expireVersionDays]
    response = s3client.put_bucket_lifecycle_configuration(
        Bucket=bucket,
        LifecycleConfiguration={ 'Rules':rules }
    )
    print("Success, note: if this bucket was created by cloudformation, you should update that CF template also.")
    return response
    

def main ():
    args = parser.parse_args()
    loglevel = args.log
    bucket = args.bucket
    days = int(args.days)
    initLogging(loglevel)
    client=boto3.client('s3', config=Config(signature_version='s3v4'))
    resource = boto3.resource('s3', config=Config(signature_version='s3v4'))
    bucketVersioning(resource, bucket,'enable')
    versionExpirePolicy(client, resource, bucket,days)
    
if __name__ == '__main__':
    main()