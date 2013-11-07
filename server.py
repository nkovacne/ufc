# -*- coding: utf-8 -*-

from twisted.internet.protocol import ServerFactory
from twisted.internet import reactor
from twisted.protocols import basic, policies
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

        log.debug('lineReceived: "%s"' % line)
        if line:
            self._buffer.append(line)
        else:
            self._process_request()
            self._buffer = []

    def _process_request(self):
        log.debug('Processing request: %s' % self._buffer)
        request = self.factory.ufc.append_to_log(self._buffer)
        action = self.factory.ufc.check_limits(request)
        self.send_action(action)

    def send_action(self, action):
        answer = "action=%s" % action
        log.debug("send_action: %s" % answer)
        self.sendLine(answer)
        self.sendLine('')

class UFCFactory(ServerFactory):
    # Crea instancias de UFCProtocol por cada conexión que se cree

    protocol = UFCProtocol

    def __init__(self, ufc):
        self.ufc = ufc

def start(ufc):
    port = reactor.listenTCP(9000, UFCFactory(ufc))
    log.info('Listening on %s' % port.getHost())
    reactor.run()

