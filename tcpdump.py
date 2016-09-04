# -*- coding: utf-8 -*-
import pymongo
import subprocess as sub
from datetime import datetime
from celery import Celery

client = pymongo.MongoClient('localhost')
db = client['tcp_python']
p = sub.Popen(('sudo', 'tcpdump', '-l'),
stdout=sub.PIPE)
for row in iter(p.stdout.readline,b''):
    db.profiles.insert_one({"not_parsed": row.rstrip()})
