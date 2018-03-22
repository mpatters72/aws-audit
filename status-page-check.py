#!/usr/bin/env python

# Audit a specific components on a statuspage.io Status Page

import json, requests, argparse

# parameters for status to check
parser = argparse.ArgumentParser()
parser.add_argument(
    '--sum_url', default='https://unsplash.statuspage.io/api/v2/summary.json',
    help='e.g. summary API URL')

parser.add_argument(
    '--components', default='API',
    help='List of comma separated components "API,CDN"')

parser.add_argument(
    '--okstatus', default='operational',
    help='List of comma separated acceptable status codes "operational,degraded_performance"')

def get_summary(url):
    """
    Download Summary JSON from status page api URL
    """
    summary = requests.get(url)
    if summary.status_code != 200:
        exit("Non 200 status code downloading summary API URL")
    name = summary.json().get('page').get('name')
    if name:
        print 'Retrieved status for: ' + str(name) + ' At: ' + url
    return summary

def check_status(summary, components, okstatus):
    """
    Look at specific components to see if expected status matches
    If one or more components has not okstatus exit non-zero
    """
    status_code = 0
    items = summary.json().get('components')
    for item in items:
        if item['name'] in components:
            if item['status'] in okstatus:
                print "OK: " + item['name'] + " " + item['status']
            else:
                print "CRIT: " + item['name'] + " " + item['status']
                status_code = 2
    exit(status_code)


def main():
    """
    Parses args, gets summary status JSON from sum_url
    Compares components you're checking vs expected result 
    """

    args = parser.parse_args()
    components = args.components.replace(" ", "").split(",")
    okstatus = args.okstatus.replace(" ", "").split(",")
    sum_url = args.sum_url

    summary = get_summary(sum_url)
    check_status(summary, components, okstatus)

if __name__ == '__main__':
    main()

