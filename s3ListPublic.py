#!/usr/bin/env python
import botocore
import boto3
import re
import json
import argparse
import logging
from botocore.client import Config

# This script is designed audit for buckets with Public ACL or Policy that are Public
# I took pieces from: https://whiletrue.run/2017/07/20/list-aws-s3-buckets-with-public-acls/

# default args will list all public/open acls and policies
parser = argparse.ArgumentParser()
parser.add_argument('-l', '--log', default='ERROR', help='loglevel, eg DEBUG, INFO, WARNING, ERROR, CRITICAL')
parser.add_argument('-p', '--pattern', default='', help='pattern in bucket name, eg static or leave blank for all buckets')

# convert lower to upper case if passed
def initLogging(loglevel):
    numeric_level = getattr(logging, loglevel.upper(), 'WARNING')
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    logging.basicConfig(level=numeric_level)

def acl_check(client, bucket, grantee):
    uri = 'http://acs.amazonaws.com/groups/global/' + str(grantee) + '/'
    try:
        acl = bucket.Acl()
        logging.warn( bucket.Acl() )
        for grant in acl.grants:
            logging.warn(str(bucket.name) + "grant: " + str(grant['Grantee']))
            if grant['Grantee']['Type'].lower() == 'group':
                if grantee in grant['Grantee']['URI']:
                    # the grant is assigned to All Users (so it is public!!!)
                    grant_permission = grant['Permission'].lower()
                    if grant_permission == 'read':
                        print(bucket.name + ' Read - ' + grantee + ' Access: List Objects')
                    elif grant_permission == 'write':
                        print(bucket.name + ' Write - ' + grantee + ' Access: Write Objects')
                    elif grant_permission == 'read_acp':
                        print(bucket.name + ' Read - ' + grantee + ' Access: Read Bucket Permissions')
                    elif grant_permission == 'write_acp':
                        print(bucket.name + ' Write - ' + grantee + ' Access: Write Bucket Permissions')
                    elif grant_permission == 'full_control':
                        print(bucket.name + ' Public ' + grantee + ': Full Control')
                    else:
                        print(bucket.name + ' Wha Happen?' + str(grant) + " " + str(grant_permission))
    except client.exceptions.NoSuchBucket as e:
        print "NoSuchBucket Error: " + bucket.name

def policy_check(client, bucket):
    try:
        bucket_policy = client.get_bucket_policy(Bucket=bucket.name)
        policy_obj = bucket_policy['Policy']
        policy = json.loads(policy_obj)
        if 'Statement' in policy:
            for p in policy['Statement']:
                if p['Principal'] == '*': # any public anonymous users!
                    print bucket.name + " " + str(p['Principal']) + " has : " + str(p['Action'])
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchBucketPolicy':
            logging.warn("No policy is applied to bucket - it's OK for bucket to not have policy")
            return 0
        else:
            raise Exception("Unexpected error: %s" % e)

#return list of bucket _objects_ emtpy list matches all buckets
def findBuckets(client, resource, pattern):
    buckets=[]
    for bucket in resource.buckets.all():
        logging.debug("bucket found: %s" , bucket.name)
        if pattern in str(bucket.name):
            logging.warn("bucket matching: %s pattern: %s", bucket.name, pattern)
            buckets.append(bucket)
            acl_check(client, bucket, 'AllUsers')
            acl_check(client, bucket, 'AuthenticatedUsers')
            policy_check(client, bucket)


def main ():
    args = parser.parse_args()
    pattern = args.pattern
    loglevel = args.log
    initLogging(loglevel)
    client=boto3.client('s3', config=Config(signature_version='s3v4'))
    resource = boto3.resource('s3', config=Config(signature_version='s3v4'))
    findBuckets(client, resource, pattern)
    
if __name__ == '__main__':
    main()
