#!/usr/bin/env python

"""
Generate random IP addresses and insert them into redis.
"""

import argparse
import random
import socket
import struct
import sys

import redis

from smithers import conf, data_types, redis_keys


parser = argparse.ArgumentParser(description='Bart throws random IPs at Lisa.')
parser.add_argument('--count', default=5000, type=int,
                    help='number of IPs')
parser.add_argument('--downloads', action='store_true',
                    help='Include downloads in generated data')
parser.add_argument('-v', '--verbose', action='store_true')

args = parser.parse_args()

r = redis.StrictRedis()

issues = data_types.types_map.keys()
if args.downloads:
    issues.append(data_types.DOWNLOAD)


def get_random_ip():
    # shamelessly stolen from the maxminddb benchmark script
    # https://github.com/maxmind/MaxMind-DB-Reader-python/blob/master/examples/benchmark.py
    return socket.inet_ntoa(struct.pack('!L', random.getrandbits(32)))


for i in xrange(args.count):
    issue = random.choice(issues)
    r.lpush(redis_keys.IPLOGS, '%s,%s' % (issue, get_random_ip()))
    if args.verbose:
        sys.stdout.write('.')
        sys.stdout.flush()
