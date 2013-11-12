#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Este script hace accounting de todos los correos que mueve postfix.
#
# Con esta información se pretende poder controlar el flujo de mensajes
# salientes de postfix.
#
#
# TODO
#  - Implementar un decorador needs_root que verifique si el usuario que ejecuta
#    el script es root (necesario para ejecutar postsuper).
#
# FIXME
#  - Aunque se libere un baneo se sigue comprobando si el usuario ha superado el
#    límite configurado. Este límite no hay modo de saltárselo.
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
from models import Log, Ban, OR
from utils import fatal_error, sendMail

import logging
log = logging.getLogger('ufc')
log.setLevel(logging.INFO)
from logging.handlers import SysLogHandler
syslog = SysLogHandler('/dev/log', facility = SysLogHandler.LOG_MAIL)
syslog.setFormatter(logging.Formatter('%(name)s: %(levelname)s %(message)s'))
log.addHandler(syslog)

config_path = '/etc/ufc.cfg'

mail_tpl = """
El usuario %s ha pretendido enviar en %s segundos más de %s mensajes.
La actividad se ha detectado en la máquina %s.
"""

class UFC():
    "ULL Flow Control"

    # Configuración del correo
    smtp_server = 'localhost'
    recipients = ['root', ]
    fqdn = socket.getfqdn()
    tls_required = True

    hold = 'HOLD bloqueado por el control de flujo.'

    def __init__(self, verbose = False, listen_tcp = True):
        if verbose:
            log.setLevel(logging.DEBUG)
        self.listen_tcp = listen_tcp
        self.configure()

    def configure(self):
        config = ConfigParser.ConfigParser()
        try:
            config.read(config_path)
        except IOError:
            log.error('Error reading configuration from %s' % config_path)
            return False

        log.info("Reading configuration from %s" % config_path)

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
            log.error('Database access error, connection string used: %s. Error: %s' % (connection_string, e))
            return False

        sqlhub.processConnection = connection
        Log.createTable(ifNotExists = True)
        Ban.createTable(ifNotExists = True)

        return True

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

    def append_to_log(self, request):
        for attrib in ('recipient_count', 'size', 'encryption_keysize'):
            if request[attrib] is not None:
                request[attrib] = int(request[attrib])

        request['request_time'] = datetime.datetime.now()
        request['expiresAt'] = request['request_time'] + datetime.timedelta(weeks=1)

        log.info(u"[%s] - %s - %s => %s" % (
            request['request_time'], request['client_address'], \
            request['sender'], request['recipient']))

        return Log(**request)

    def is_banned(self, user):
        bans = Ban.select(Ban.q.sender == user).\
            filter(OR(Ban.q.expires_at == None, Ban.q.expires_at > datetime.datetime.now()))
        if not bans.count():
            return False
        return bans

    def ban_user(self, user):
        Ban(
            sender = user,
            created = datetime.datetime.now(),
            host = self.fqdn
            )
        sendMail(
            'Bloqueado el envío de correo del usuario %s' % user,
            mail_tpl % (user, self.max_time, self.max_email, self.fqdn),
            self.smtp_server,
            self.tls_required,
            self.recipients,
            user
        )

    def unban_user(self, user):
        bans = self.is_banned(user)
        if not bans:
            log.warning("The user %s doesn't have bans to release" % user)
        else:
            log.info("Releasing %s bans for user %s" % (bans.count(), user))
            now = datetime.datetime.now()
            for b in bans:
                log.debug("Setting expire time to %s to the ban created at %s in %s" % (now, b.created, b.host))
                b.expires_at = now

    def release_mail(self, user):
        """
            Unhold mail from the user
        """
        pass

    def remove_mail(self, user):
        """
            Remove mail from the user
        """
        pass

    def check_limits(self, request):
        """
            Con la información que nos manda postfix que tenemos en request tenemos que
            tomar la decisión de qué hacer.

            Las acciones que podemos ordenar son todas las que se pueden poner en un access map:
            http://www.postfix.org/access.5.html
        """
        action = 'DUNNO'
        sender = request['sender']

        if self.is_banned(sender):
            log.debug("Intento de envío de correo de un usuario baneado: %s" % sender)
            action = self.hold
        else:
            time = request['request_time'] - datetime.timedelta(seconds = self.max_time)
            sended_emails = Log.select(Log.q.sender == sender).filter(Log.q.request_time > time).count()
            if sended_emails >= self.max_email:
                log.info("Bloqueando correo del usuario %s por enviar %d correos en menos de %d segundos" % \
                    (sender, sended_emails, self.max_time))
                action = self.hold
                self.ban_user(sender)

        return action

    def check(self, lines):
        request = dict([line.split('=', 1) for line in lines if line])
        self.append_to_log(request)
        return self.check_limits(request)

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
        if self.listen_tcp:
            import server
            server.start(self)
        else:
            lines = self.read_lines_from_stdin()
            print "action=%s\n" % self.check(lines)

def main(options):
    ufc = UFC(options.verbose, not options.stdin)
    if options.purge:
        ufc.purge()
    elif options.unban_email:
        ufc.unban_user(options.unban_email)
        if options.release:
            ufc.release_mail(options.unban_email)
        elif options.remove:
            ufc.remove_mail(options.unban_email)
    else:
        ufc.process()

if __name__ == "__main__":
    try:
        parser = OptionParser()
        parser.add_option("-p", "--purge", dest="purge", action="store_true", help="Purge log database", default=False)
        parser.add_option("-v", "--verbose", dest="verbose", action="store_true", help="Verbose", default=False)
        parser.add_option("-d", "--daemon", dest="daemon", action="store_true", help="Daemonize", default=False)
        parser.add_option("-s", "--stdin", dest="stdin", action="store_true", help="Read input from STDIN (no listen TCP)", default=False)
        parser.add_option("--unban", dest="unban_email", help="Unban email (implies --no-daemon)")
        parser.add_option("--release", dest="release", help="Release mail from hold sent by unbanned user")
        parser.add_option("--remove", dest="remove", help="Remove mail from hold sent by unbanned user")
        options, args = parser.parse_args()

        if options.daemon:
            with daemon.DaemonContext():
                main(options)
        else:
            main(options)

    except Exception, e:
        fp = StringIO()
        traceback.print_exc(file=fp)
        log.error('Excepcion no controlada del tipo %s: %s' % (type(e), e))
        log.error('%s' % fp.getvalue())
        fatal_error()

