#!/usr/bin/env python

from netaddr import *
from ipaddress import *

# This converts a list of CIDR blocks into 8, 16, 24, or 32 networks (e.g. /17 is broken down into 128 /24 networks)
# WAF IPSet rules can only accept standard that network notation
# http://docs.aws.amazon.com/waf/latest/APIReference/API_IPSet.html
# http://bradthemad.org/tech/notes/cidr_subnets.php
# https://docs.python.org/3/library/ipaddress.html

# format of file IR,5.202.0.0/16
EMBARGOED_FILE = open('EmbargoedCountries_20170606.csv', 'r')

def smallblocks(block, smallermask):
    networks = list(ip_network(unicode(block)).subnets(new_prefix=smallermask))
    return networks

def checkmask(block, mask):
    networks = []
    if mask > 16 and mask < 24:
        networks = smallblocks(block, 24)
    elif mask > 8 and mask < 16:
        networks = smallblocks(block, 16)
    elif mask > 0 and mask < 8:
        networks = smallblocks(block, 8)
    else:
        print "Invalid mask for breaking down to smaller mask: " + block + str(mask)
        exit(1)
    return networks

for line in EMBARGOED_FILE:
    if not line.startswith("#"):
        if not 'Republic' in line:
            country, ip_addr, mask = line.rstrip().replace('/', ',').split(',')
            block = str(ip_addr + '/' + mask)
            mask = int(mask)
            if mask in [8, 16, 24, 32]:
                print block
            elif mask > 24 and mask < 32:
                for ip in IPNetwork(block):
                    print '%s/32' % ip
            elif mask > 0 and mask < 24:
                networks = checkmask(block, mask)
                for net in networks:
                    print net
            else:
                print "Something went wrong: " + block + str(mask)
                exit(1)
