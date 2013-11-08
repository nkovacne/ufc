#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Este script hace accounting de todos los correos que mueve postfix.
#
# Con esta información se pretende poder controlar el flujo de mensajes
# salientes de postfix.
#

import daemon
import datetime
import sys
import os
import ConfigParser
import socket
from optparse import OptionParser
from cStringIO import StringIO
import traceback
from sqlobject import sqlhub, connectionForURI
from models import Log, Ban
from utils import fatal_error, sendMail

import logging
log = logging.getLogger('ufc')
log.setLevel(logging.INFO)
from logging.handlers import SysLogHandler
syslog = SysLogHandler('/dev/log', facility = SysLogHandler.LOG_MAIL)
syslog.setFormatter(logging.Formatter('%(name)s: %(levelname)s %(message)s'))
log.addHandler(syslog)

class UFC():
    "ULL Flow Control"

    # Configuración del correo
    smtp_server = 'localhost'
    recipients = ['root', ]
    fqdn = socket.getfqdn()
    tls_required = True

    def __init__(self, verbose = False, interactive = False):
        config = ConfigParser.ConfigParser()
        try:
            config.read('/etc/ufc.cfg')
        except IOError:
            fatal_error(u'Error leyendo la configuración')

        #log_filename = self.get_config(config, 'log', 'filename')
        #log.addHandler(logging.FileHandler(log_filename))
        if verbose:
            log.setLevel(logging.DEBUG)

        self.interactive = interactive
        self.smtp_server = self.get_config(config, 'smtp', 'server', self.smtp_server)
        self.recipients = self.get_config(config, 'smtp', 'recipients', self.recipients)
        if type(self.recipients) == str:
            self.recipients = self.recipients.split(',')
        self.max_time = int(self.get_config(config, 'limits', 'max_time'))
        self.max_email = int(self.get_config(config, 'limits', 'max_email'))

        connection_string = self.get_config(config, 'database', 'connection_string')
        try:
            connection = connectionForURI(connection_string)
        except Exception, e:
            fatal_error(u'Cadena de conexión incorrecta: %s. Error: %s' % (connection_string, e))

        sqlhub.processConnection = connection
        Log.createTable(ifNotExists = True)
        Ban.createTable(ifNotExists = True)

    def get_config(self, config, section, option, default = None):
        log.debug("Reading [%s]:%s from config" % (section, option))
        try:
            value = config.get(section, option)
            log.debug("Found value: %s" % value)
            return value
        except ConfigParser.NoSectionError, e:
            if default is not None:
                log.debug('Not found, using default: %s' % default)
                return default
            fatal_error('Error: %s' % e)
        except ConfigParser.NoOptionError, e:
            if default is not None:
                log.debug('Not found, using default: %s' % default)
                return default
            fatal_error('Error: %s' % e)

    def append_to_log(self, stdin_lines):
        request_dict = dict([line.split('=', 1) for line in stdin_lines if line])

        for attrib in ('recipient_count', 'size', 'encryption_keysize'):
            try:
                if request_dict[attrib] is not None:
                    request_dict[attrib] = int(request_dict[attrib])
            except KeyError, e:
                fatal_error('Error parseando la entrada %s: %s' % (attrib, e))

        request_dict['request_time'] = datetime.datetime.now()
        request_dict['expiresAt'] = request_dict['request_time'] + datetime.timedelta(weeks=1)

        log.info(u"[%s] - %s - %s => %s" % (
            request_dict['request_time'], request_dict['client_address'], \
            request_dict['sender'], request_dict['recipient']))

        Log(**request_dict)

        return request_dict

    def check_limits(self, request):
        """
            Con la información que nos manda postfix que tenemos en request tenemos que
            tomar la decisión de qué hacer.

            Las acciones que podemos ordenar son todas las que se pueden poner en un access map:
            http://www.postfix.org/access.5.html
        """
        action = 'DUNNO'
        sender = request['sender']
        if sender.endswith("@ull.es"):
            time = request['request_time'] - datetime.timedelta(seconds = self.max_time)
            sended_emails = Log.select(Log.q.sender == sender).filter(Log.q.request_time > time).count()
            if sended_emails >= self.max_email:
                sendMail(
                    'Control de flujo de correo en %s' % self.fqdn,
                    'El usuario %s ha pretendido enviar en %s segundos más de %s mensajes.' % (sender, self.max_time, self.max_email),
                    self.smtp_server,
                    self.tls_required,
                    self.recipients,
                    sender
                )
                action = 'HOLD bloqueado por el control de flujo. Demasiados mensajes enviados en los ultimos %s segundos.' % self.max_time
                log.warn("Bloqueando correo del usuario %s por enviar %d correos en menos de %d segundos" % \
                    (sender, sended_emails, self.max_time))
        return action

    def purge(self):
        log.info("Expirando entradas antiguas en el Log")
        for e in Log.select(Log.q.expiresAt < datetime.datetime.now()):
            e.destroySelf()
        return True

    def read_line_from_stdin(self):
        line = ''
        for c in sys.stdin.readline():
            if c == '\n':
                break
            line += c
        return line.strip()

    def read_lines_from_stdin(self):
        lines = []
        while True:
            line = self.read_line_from_stdin()
            log.debug("Stdin: %s" % line)
            if line == "":
                break
            lines.append(line)
        return lines

    def process(self):
        if self.interactive:
            lines = self.read_lines_from_stdin()
            request = self.append_to_log(lines)
            print "action=%s\n" % self.check_limits(request)
        else:
            import server
            server.start(self)

def main(options, interactive = False):
    ufc = UFC(options.verbose, interactive)
    if options.purge:
        ufc.purge()
    else:
        ufc.process()

if __name__ == "__main__":
    try:
        parser = OptionParser()
        parser.add_option("-p", "--purge", dest="purge", action="store_true", help="Purge log database (implies --no-daemon)", default=False)
        parser.add_option("-v", "--verbose", dest="verbose", action="store_true", help="Verbose", default=False)
        parser.add_option("-n", "--no-daemon", dest="no_daemon", action="store_true", help="No daemonize", default=False)
        options, args = parser.parse_args()

        if options.no_daemon or options.purge:
            main(options, interactive = True)
        else:
            with daemon.DaemonContext():
                main(options)

    except Exception, e:
        fp = StringIO()
        traceback.print_exc(file=fp)
        log.error('Excepcion no controlada del tipo %s: %s' % (type(e), e))
        log.error('%s' % fp.getvalue())
        fatal_error()

