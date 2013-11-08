# -*- coding: utf-8 -*-

import sys
import smtplib

import logging
log = logging.getLogger('ufc')

msg_tpl = """Content-Type: text/plain; charset="utf-8"
Subject: %s

%s
"""
def fatal_error(msg = None):
    if msg is not None:
        log.error(msg)
    print "action=dunno\n\n"
    sys.exit(0)

def sendMail(subject, body, smtp_server, tls_required, recipients, sender):
    log.debug('Enviando correo a %s' % recipients)

    session = smtplib.SMTP(smtp_server)
    if tls_required:
        session.starttls()

    msg = msg_tpl % (subject, body)
    smtpresult = session.sendmail(sender, recipients, msg)
    if smtpresult:
        errstr = ""
        for recip in smtpresult.keys():
            errstr = """No he podido entregar el correo a: %s

El servidor ha dicho: %s
%s

%s""" % (recip, smtpresult[recip][0], smtpresult[recip][1], errstr)
        raise smtplib.SMTPException, errstr

