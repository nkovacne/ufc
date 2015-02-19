# -*- coding: utf-8 -*-

from sqlalchemy import Table, Column, Integer, String, DateTime, MetaData
from sqlalchemy.orm import mapper
import datetime

metadata = MetaData()

tabla_log = Table('log', metadata,
    Column('id', Integer, primary_key=True, nullable=False, autoincrement=True),
    Column('helo_name', String(length=100), nullable=False),
    Column('queue_id', String(length=20), nullable=True, default=None),
    Column('sender', String(length=256), nullable=False),
    Column('recipient', String(length=256), nullable=False),
    Column('client_address', String(length=15), nullable=False),
    Column('client_name', String(length=256), nullable=False),
    Column('reverse_client_name', String(length=256), nullable=False),
    Column('sasl_username', String(length=100), nullable=True, default=None),
    Column('size', Integer, nullable=True, default=None),
    Column('request_time', DateTime, nullable=True),
    Column('expires_at', DateTime, nullable=True),
    Column('real_sender', String(length=256), nullable=False, index=True)
)

tabla_ban = Table('ban', metadata,
    Column('id', Integer, primary_key=True, nullable=False, autoincrement=True),
    Column('sender', String(length=256), nullable=False),
    Column('created', DateTime, nullable=False, default=datetime.datetime.utcnow),
    Column('expires_at', DateTime, nullable=True),
    Column('host', String(length=256), nullable=False)
)

class Log(object):
    def __init__(self, valuearr):
        self.helo_name = valuearr['helo_name']
        self.queue_id = valuearr['queue_id']
        self.sender = valuearr['sender']
        self.recipient = valuearr['recipient']
        self.client_address = valuearr['client_address']
        self.client_name = valuearr['client_name']
        self.reverse_client_name = valuearr['reverse_client_name']
        self.sasl_username = valuearr['sasl_username']
        self.size = valuearr['size']
        self.request_time = valuearr['request_time']
        self.expires_at = valuearr['expiresAt']
        self.real_sender = valuearr['real_sender']

    def __repr__(self):
        return "<%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s>" % (self.helo_name, self.queue_id, self.sender, self.recipient, self.client_address, self.client_name, self.reverse_client_name, self.sasl_username, self.size, self.request_time, self.expiresAt, self.real_sender)

class Ban(object):
    def __init__(self, sender, created, host, expires_at=None):
        self.sender = sender
        self.created = created
        self.expires_at = expires_at
        self.host = host

    def __repr__(self):
        return "<%s, %s, %s>" % (self.sender, self.expires_at, self.host)

mapper(Log, tabla_log)
mapper(Ban, tabla_ban)
