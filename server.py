# -*- coding: utf-8 -*-

from twisted.internet.protocol import ServerFactory
from twisted.internet import reactor, threads
from twisted.protocols import basic, policies
from twisted.internet.defer import Deferred
import time

import logging
log = logging.getLogger('ufc')

class UFCProtocol(basic.LineReceiver, policies.TimeoutMixin):
    """
        This is an implementation of Postfix policy protocol
    """

    timeout = 600
    delimiter = '\n'

    def __init__(self):
        self._buffer = []
    
    def connectionMade(self):
        self.setTimeout(self.timeout)
        try:
            self._peer_ip, self._peer_port = self.transport.getHandle().getpeername()
        except:
            self._peer_ip, self._peer_port = None, None
        log.debug('Connect from [%s]:%s' % (self._peer_ip, self._peer_port))

    def connectionLost(self, reason):
        log.debug('Disconnect from [%s]:%s; %s' % (self._peer_ip, self._peer_port, reason))

    def lineReceived(self, line):
        self.resetTimeout()

        #log.debug('lineReceived: "%s"' % line)
        if line:
            self._buffer.append(line)
        else:
            self._process_request()
            self._buffer = []

    def _process_request(self):
        log.debug('Processing request: %s' % self._buffer)
        # Run check in a thread so database access don't block our twisted reactor
        d = threads.deferToThread(self.factory.check, self._buffer)
        d.addCallback(self._callback)
        d.addErrback(self._errback)

    def _callback(self, action):
        self._send_action(action)

    def _errback(self, reason):
        log.error("Processing request error: %s" % reason)
        self._send_action('DUNNO')

    def _send_action(self, action):
        answer = "action=%s" % action
        log.debug("send_action: %s" % answer)
        self.sendLine(answer)
        self.sendLine('')

class UFCFactory(ServerFactory):
    # Crea instancias de UFCProtocol por cada conexión que se cree

    protocol = UFCProtocol

    def __init__(self, ufc):
        self.ufc = ufc

    def check(self, lines):
        request = self.ufc.append_to_log(lines)
        return self.ufc.check_limits(request)

def start(ufc):
    port = reactor.listenTCP(9000, UFCFactory(ufc))
    log.info('Listening on %s' % port.getHost())
    reactor.run()

