#!/usr/bin/env python

# Audit Subdomain Takeover risk from 1 or more AWS accounts
# Find Route53 records pointing to CloudFront and whether or not all CF Aliases are registered
# Note: All aliases in chain are found by DNS resolution and Cloudfront status checked by CIDR block
# Option to provide list of aws profiles from ~/.aws/credentials if desired
# https://labs.detectify.com/2014/10/21/hostile-subdomain-takeover-using-herokugithubdesk-more/

import json
import logging
import argparse
import socket
import urllib
import netaddr
import docstring
import boto3

# get AWS accounts to run on
PARSER = argparse.ArgumentParser()
PARSER.add_argument(
    '--profiles', default='default',
    help='List of comma separated aws profiles "dev,stage,prod"')

def get_cf_blks():
    """
    Download CloudFront CIDR blocks
    http://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/LocationsOfEdgeServers.html
    """
    url = 'http://d7uri8nf7uskq.cloudfront.net/tools/list-cloudfront-ips'
    response = urllib.urlopen(url)
    data = json.loads(response.read())
    return data['CLOUDFRONT_GLOBAL_IP_LIST']

def ip_in_block(ips, blocks):
    """ Pass list of IPs and CIDR blocks, check if one or more IP is in a CIDR block """
    in_block = 'no'
    for ip in ips:
        logging.debug("ip: " + ip)
        for blk in blocks:
            if netaddr.IPAddress(ip) in netaddr.IPNetwork(blk):
                in_block = 'yes'
    return in_block

def add_cf_aliases(profile):
    """ Gets all CF distributions from AWS and adds DNS aliases to list """
    cfaliases = []
    boto3.setup_default_session(profile_name=profile)
    client = boto3.client('cloudfront')
    response = client.list_distributions()
    distributions = response['DistributionList']['Items']
    for dist in distributions:
        if dist['Aliases']['Quantity'] > 0:
            cfaliases[1:1] = (dist['Aliases']['Items'])
            logging.debug(str(dist['Aliases']['Items']))
    return cfaliases

def return_a_and_cnames(profile):
    """ Gets all route53 zones, calls get_records, returns A and CNAME records lists """
    boto3.setup_default_session(profile_name=profile)
    client = boto3.client('route53')
    response = client.list_hosted_zones()
    zones = response['HostedZones']
    cname_records = []
    a_records = []
    for zone in zones:
        logging.info("Retrieving R53 Zone: " + str(zone))
        cname_records = cname_records + get_records(profile, zone['Id'], 'CNAME')
        a_records = a_records + get_records(profile, zone['Id'], 'A')
    return a_records, cname_records

def get_records(profile, zoneid, rrtype):
    """ get records for specified ID and record type """
    boto3.setup_default_session(profile_name=profile)
    client = boto3.client('route53')
    response = client.list_resource_record_sets(HostedZoneId=zoneid)
    rrs = response['ResourceRecordSets']
    record_list = []
    for rr in rrs:
        if rr['Type'] == rrtype:
            record_list.append(rr['Name'])
    return record_list

def get_dns(domain):
    """
    inspired by LoanWolffe http://stackoverflow.com/questions/3837744/how-to-resolve-dns-in-python
    This method returns 3 lists, hostname, aliases/cnames,
    and one or more IP address strings that respond
    as the given domain name
    """
    try:
        data = socket.gethostbyname_ex(domain)
        host = data[0]
        cnames = data[1]
        ipx = data[2]
        return host, cnames, ipx
    except Exception:
        return [False, False, False]

def audit_records(records, cfcidrblocks, cf_aliases):
    """
    Pass list or records, Cloudfront CIDR blocks, and list of Cloudfront Aliases
    It'll check if it's pointed at cloudfront and if we have all DNS entries
    registered as a cloudfront domain alias
    """
    for rec in sorted(records):
        rec = rec.rstrip('.')
        logging.debug("Getting DNS info for: " + rec)
        host, cnames, ipx = get_dns(rec)
        logging.debug(host, cnames, ipx)
        # if not empty
        if ipx:
            # convert to unicode
            uipx = [unicode(item) for item in ipx]
            if ip_in_block(uipx, cfcidrblocks) == 'yes':
                logging.info(rec + ": points to cloudfront")
                if cnames:
                    for cname in cnames:
                        cname = cname.rstrip('.')
                        if cname in cf_aliases:
                            logging.info(rec + ": alias: " + cname + " is in our CF Distros")
                        else:
                            print "RISK: " + rec + ": alias: " + cname + " not in our CF Distros"
                else:
                    if rec in cf_aliases:
                        logging.info("OK: " + rec + " is in our CF Distros")
                    else:
                        print "RISK: " + rec + " not in our CF Distros"

def main():
    """
    Creates lists of Cloudfront Domain Aliases registered across AWS accounts
    Checks if any Route53 record resolved to cloudfront CIDR blocks
    If so checks our cloudfront domain aliases list to see if it is registered
    """
    logging.basicConfig(level=logging.WARN)
    logging.getLogger('boto3').setLevel(logging.WARN)
    logging.getLogger('botocore').setLevel(logging.WARN)

    args = PARSER.parse_args()
    profiles = args.profiles.replace(" ", "").split(",")
    # get List of CF CIDR blocks
    logging.info("Downloading CloudFront CIDR blocks")
    cfcidrblocks = get_cf_blks()
    cf_aliases = []
    # collect CF aliases from all profiles into 1 list
    for profile in profiles:
        print "Retrieving CloudFront data from AWS profile: " + profile
        cf_aliases = cf_aliases + add_cf_aliases(profile)
    # remove duplicates
    cf_aliases = list(set(cf_aliases))
    logging.debug(cf_aliases)
    # audit records
    logging.debug("#### CNAME and A records ####")
    for profile in profiles:
        print "Auditing " + profile + " records"
        a_records, cname_records = return_a_and_cnames(profile)
        audit_records(a_records, cfcidrblocks, cf_aliases)
        audit_records(cname_records, cfcidrblocks, cf_aliases)

if __name__ == '__main__':
    main()
