# -*- coding: utf-8 -*-
import pymongo
import subprocess as sub
from datetime import datetime

client = pymongo.MongoClient('localhost')

db = client['tcp_python']

p = sub.Popen(('sudo', 'tcpdump', '-l'),
                    stdout=sub.PIPE)

for row in iter(p.stdout.readline,b''):
    pack = row.rstrip()
    type_pack = pack.split('.')[0]
    data = pack.split()[1:len(pack)-1]
    #db.child('data').child(type_pack).push(data)
    temp = data[1].split('.')
    s_ip = ".".join(temp[0:len(temp)-1])
    s_port = temp[len(temp)-1]
    temp = data[3].split('.')
    d_ip = ".".join(temp[0:len(temp)-1])
    d_port = temp[len(temp)-1]

    post = {"type": datetime.now(),
            "source": s_ip,
            "destiny": d_ip,
            "source_port": s_port,
            "destiny_port": d_port,
           }
    posts = db.posts
    post_id = posts.insert_one(post).inserted_id
