# -*- coding: utf-8 -*-
import pymongo
import subprocess as sub
from datetime import datetime


class tcpdaemon():

    def __init__(self):
        self.client = pymongo.MongoClient('localhost')
        self.db = client['tcp_python']
        self.p = None
        self.parse_data()

    def start_tcp(self):
        self.p = sub.Popen(('sudo', 'tcpdump', '-l'),
                            stdout=sub.PIPE)
        for row in iter(self.p.stdout.readline,b''):
            self.db.posts.insert_one({"not_parsed": row})

    def stop_tcp(self):
        if self.p is not None:
            self.p.kill()
        return False

    def parse_data(self):
        posts = self.db.posts.find('not_parsed')

        for post in posts:
            pack = post['not_parsed'].rstrip()
            post_id = post.get('_id')
            type_pack = pack.split('.')[0]
            data = pack.split()[1:len(pack)-1]

            temp = data[1].split('.')
            s_ip = ".".join(temp[0:len(temp)-1])
            s_port = temp[len(temp)-1]

            temp = data[3].split('.')
            d_ip = ".".join(temp[0:len(temp)-1])
            d_port = temp[len(temp)-1]

            new = {"date": type_pack,
            "source": s_ip,
            "destiny": d_ip,
            "source_port": s_port,
            "destiny_port": d_port,
            }
            self.db.posts.insert_one(new)
            self.db.posts.remove_one({'_id':post_id})
