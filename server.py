# -*- coding: utf-8 -*-

from twisted.internet.protocol import ServerFactory
from twisted.internet import reactor, threads
from twisted.protocols import basic, policies
from twisted.internet.defer import Deferred
from twisted.internet.error import ConnectionLost
import time
import signal

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
        log.debug('Connect from %s' % self.transport.getPeer())

    def connectionLost(self, reason):
        if reason.type != ConnectionLost:
            log.debug('Disconnect from %s' % self.transport.getPeer())
        else:
            log.error('Disconnect from %s: %s' % (self.transport.getPeer(), reason))

    def lineReceived(self, line):
        self.resetTimeout()

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

        signal.signal(signal.SIGHUP, self._sighup_handler)

    def _sighup_handler(self, signum, frame):
        self.ufc.configure()

    def check(self, lines):
        return self.ufc.check(lines)

def start(ufc):
    port = reactor.listenTCP(9000, UFCFactory(ufc))
    log.info('Listening on %s' % port.getHost())
    reactor.run()

