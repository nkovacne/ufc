# -*- coding: utf-8 -*-

from sqlobject import *

class Log(SQLObject):
    sender_index = DatabaseIndex('sender')
    recipient_index = DatabaseIndex('recipient')

    request = StringCol(length=100)                                 # smtpd_access_policy
    protocol_state = StringCol(length=20)                           # RCPT
    protocol_name = StringCol(length=20)                            # SMTP
    helo_name = StringCol(length=100)                               # some.domain.tld
    queue_id = StringCol(length=20, notNone=False)                  # 8045F2AB23
    sender = StringCol(length=256)                                  # foo@bar.tld
    recipient = StringCol(length=256)                               # bar@foo.tld
    recipient_count = IntCol()                                      # 0
    client_address = StringCol(length=15)                           # 1.2.3.4
    client_name = StringCol(length=256)                             # another.domain.tld
    reverse_client_name = StringCol(length=256)                     # another.domain.tld
    instance = StringCol(length=40)                                 # 123.456.7
    # Postfix version 2.2 and later:
    sasl_method = StringCol(length=20, notNone=False)               # plain
    sasl_username = StringCol(length=100, notNone=False)            # you
    sasl_sender = StringCol(length=100, notNone=False)              # 
    size = IntCol(notNone=False)                                    # 12345
    ccert_subject = StringCol(length=256, notNone=False)            # solaris9.porcupine.org
    ccert_issuer = StringCol(length=256, notNone=False)             # Wietse+20Venema
    ccert_fingerprint = StringCol(length=256, notNone=False)        # C2:9D:F4:87:71:73:73:D9:18:E7:C2:F3:C1:DA:6E:04
    ccert_pubkey_fingerprint = StringCol(length=256, notNone=False) # C2:9D:F4:87:71:73:73:D9:18:E7:C2:F3:C1:DA:6E:04
    # Postfix version 2.3 and later:
    encryption_protocol = StringCol(length=20, notNone=False)       # TLSv1/SSLv3
    encryption_cipher = StringCol(length=100, notNone=False)        # DHE-RSA-AES256-SHA
    encryption_keysize = IntCol(notNone=False)                      # 256
    etrn_domain = StringCol(length=256, notNone=False)
    # Postfix version 2.5 and later:
    stress = StringCol(length=256, notNone=False)
    request_time = DateTimeCol()
    expiresAt = DateTimeCol()

class Ban(SQLObject):
    sender = StringCol(length=256)                      # foo@bar.tld
    initial_time = DateTimeCol()
    expires_at = DateTimeCol()

