# -*- coding: utf-8 -*-
"""
Start tcpdump and save data as a string in a mongodb
"""

import pymongo
import subprocess as sub
from datetime import datetime
from celery import Celery

client = pymongo.MongoClient('localhost')
db = client['tcp_python']
p = sub.Popen(('sudo', 'tcpdump', '-l'),
stdout=sub.PIPE)
for row in iter(p.stdout.readline,b''):
    db.full_rows.insert_one({"not_parsed": row.rstrip()})
