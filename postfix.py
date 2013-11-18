#!/usr/bin/python
# -*- coding: utf-8 -*-

import subprocess
import re

import logging
log = logging.getLogger('ufc')

mailq_cmd = '/usr/bin/mailq'
postsuper_cmd = '/usr/sbin/postsuper'

ACTIVE_QUEUE = 'active'
HOLD_QUEUE = 'hold'
DEFERRED_QUEUE = 'deferred'

status_map = {
    '*': ACTIVE_QUEUE,
    '!': HOLD_QUEUE,
    }

def status2queue(status):
    if status: 
        return status_map[status]
    return DEFERRED_QUEUE

def mailq(sender = None, status = None):
    r = re.compile(r"""^
                       (?P<queue_id>\w+)(?P<status>[!*]?)\s+
                       (?P<size>\d+)\s+
                       (?P<date>.{19})\s+
                       (?P<sender>\S+)""", re.X)
    msgs = {}
    for line in subprocess.check_output([mailq_cmd]).splitlines():
        m = r.match(line)
        if m:
            msg = {
                'status': status2queue(m.group('status')),
                'size': m.group('size'),
                'date': m.group('date'),
                'sender': m.group('sender'),
                }
            if (not sender or sender == msg['sender']) and \
               (not status or status == msg['status']):
                msgs[m.group('queue_id')] = msg
    return msgs

def release_mail(queue_ids):
    """
        Release mail from hold
    """
    log.info("Releasing from hold %d messages: %s" % (len(queue_ids), queue_ids))
    p = subprocess.Popen([postsuper_cmd, '-H', '-'], stdin = subprocess.PIPE)
    p.communicate('\n'.join(queue_ids))

def remove_mail(queue_ids):
    """
        Remove mail from Postfix queue
    """
    log.info("Removing %d messages: %s" % (len(queue_ids), queue_ids))
    p = subprocess.Popen([postsuper_cmd, '-d', '-'], stdin = subprocess.PIPE)
    p.communicate('\n'.join(queue_ids))

if __name__ == "__main__":
    print mailq()
