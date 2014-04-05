#!/usr/bin/env python

import argparse
import logging
import signal
import sys
import time

from redis import RedisError, StrictRedis
from statsd import StatsClient

from smithers import conf
from smithers.conf import redis_keys as rkeys


log = logging.getLogger('milhouse')

parser = argparse.ArgumentParser(description='Milhouse makes things Lisa tells him to.')
parser.add_argument('--log', default=conf.LOG_LEVEL, metavar='LOG_LEVEL',
                    help='Log level (default: %s)' % conf.LOG_LEVEL)
parser.add_argument('-v', '--verbose', action='store_true')
args = parser.parse_args()

logging.basicConfig(level=getattr(logging, args.log.upper()),
                    format='%(asctime)s: %(message)s')

redis = StrictRedis()
statsd = StatsClient(host=conf.STATSD_HOST,
                     port=conf.STATSD_PORT,
                     prefix=conf.STATSD_PREFIX)

# has the system requested shutdown
KILLED = False


def handle_signals(signum, frame):
    # NOTE: Makes this thing non-thread-safe
    # Should not be too difficult to fix if we
    # need/want threads.
    global KILLED
    KILLED = True
    log.info('Attempting to shut down')


# register signals
signal.signal(signal.SIGHUP, handle_signals)
signal.signal(signal.SIGINT, handle_signals)
signal.signal(signal.SIGTERM, handle_signals)


def get_timestamps_to_process():
    """Return the timestamp(s) ready to output to JSON.

    Basic idea is:

    1. Get all but the most recent 2 timestamps from the
       redis sorted set. This should allow for them to be
       sure to be done filling.
    2. Do the same for the sorted set for share data.
    3. Cast these lists as sets.
    4. Get the intersection of these sets.
    5. Process all of the timestamps from the intersection.
    """
    map_set = set(int(ts) for ts in redis.zrange(rkeys.MAP_TIMESTAMPS, 0, -3))
    share_set = set(int(ts) for ts in redis.zrange(rkeys.SHARE_TIMESTAMPS, 0, -3))
    intersection = map_set & share_set
    return sorted(list(intersection))


def main():
    counter = 0

    while True:
        if KILLED:
            log.info('Shutdown successful')
            return 0

        print get_timestamps_to_process()

        # don't run constantly since we'll only have something
        # to do every ~1 minute
        time.sleep(20)


if __name__ == '__main__':
    sys.exit(main())
