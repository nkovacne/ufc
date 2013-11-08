# -*- coding: utf-8 -*-

from sqlobject import *

class Log(SQLObject):
    sender_index = DatabaseIndex('sender')
    recipient_index = DatabaseIndex('recipient')

    request = StringCol(length=100)                                 # smtpd_access_policy
    protocol_state = StringCol(length=20)                           # RCPT
    protocol_name = StringCol(length=20)                            # SMTP
    helo_name = StringCol(length=100)                               # some.domain.tld
    queue_id = StringCol(length=20, notNone=False, default=None)    # 8045F2AB23
    sender = StringCol(length=256)                                  # foo@bar.tld
    recipient = StringCol(length=256)                               # bar@foo.tld
    recipient_count = IntCol()                                      # 0
    client_address = StringCol(length=15)                           # 1.2.3.4
    client_name = StringCol(length=256)                             # another.domain.tld
    reverse_client_name = StringCol(length=256)                     # another.domain.tld
    instance = StringCol(length=40)                                 # 123.456.7
    # Postfix version 2.2 and later:
    sasl_method = StringCol(length=20, notNone=False, default=None)               # plain
    sasl_username = StringCol(length=100, notNone=False, default=None)            # you
    sasl_sender = StringCol(length=100, notNone=False, default=None)              # 
    size = IntCol(notNone=False, default=None)                                    # 12345
    ccert_subject = StringCol(length=256, notNone=False, default=None)            # solaris9.porcupine.org
    ccert_issuer = StringCol(length=256, notNone=False, default=None)             # Wietse+20Venema
    ccert_fingerprint = StringCol(length=256, notNone=False, default=None)        # C2:9D:F4:87:71:73:73:D9:18:E7:C2:F3:C1:DA:6E:04
    ccert_pubkey_fingerprint = StringCol(length=256, notNone=False, default=None) # C2:9D:F4:87:71:73:73:D9:18:E7:C2:F3:C1:DA:6E:04
    # Postfix version 2.3 and later:
    encryption_protocol = StringCol(length=20, notNone=False, default=None)       # TLSv1/SSLv3
    encryption_cipher = StringCol(length=100, notNone=False, default=None)        # DHE-RSA-AES256-SHA
    encryption_keysize = IntCol(notNone=False, default=None)                      # 256
    etrn_domain = StringCol(length=256, notNone=False, default=None)
    # Postfix version 2.5 and later:
    stress = StringCol(length=256, notNone=False, default=None)
    request_time = DateTimeCol()
    expiresAt = DateTimeCol()

class Ban(SQLObject):
    sender = StringCol(length=256)                      # foo@bar.tld
    created = DateTimeCol()
    expires_at = DateTimeCol(notNone=False, default=None)
    host = StringCol(length=256)                        # Host that banned the user

