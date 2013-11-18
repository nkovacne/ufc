# -*- coding: utf-8 -*-

from sqlobject import *

class Log(SQLObject):
    sender_index = DatabaseIndex('real_sender')

    helo_name = StringCol(length=100)                               # some.domain.tld
    queue_id = StringCol(length=20, notNone=False, default=None)    # 8045F2AB23
    sender = StringCol(length=256)                                  # foo@bar.tld
    recipient = StringCol(length=256)                               # bar@foo.tld
    client_address = StringCol(length=15)                           # 1.2.3.4
    client_name = StringCol(length=256)                             # another.domain.tld
    reverse_client_name = StringCol(length=256)                     # another.domain.tld
    # Postfix version 2.2 and later:
    sasl_username = StringCol(length=100, notNone=False, default=None)            # you
    size = IntCol(notNone=False, default=None)                                    # 12345
    request_time = DateTimeCol()
    expiresAt = DateTimeCol()
    real_sender = StringCol(length=256)

class Ban(SQLObject):
    sender = StringCol(length=256)                      # foo@bar.tld
    created = DateTimeCol()
    expires_at = DateTimeCol(notNone=False, default=None)
    host = StringCol(length=256)                        # Host that banned the user

