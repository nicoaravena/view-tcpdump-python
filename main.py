# -*- coding: utf-8 -*-
"""
Tcpdump package parser and viewer with flask
tcpdump package line structure:
date src > dst: flags data-seqno ack window urgent options
more info http://www.tcpdump.org/manpages/tcpdump.1.html
"""

import pymongo
import os
import flask
import subprocess as sub
from flask_paginate import Pagination
from bson.son import SON

client = pymongo.MongoClient()
db = client['tcp_python']

app = flask.Flask(__name__)

app.secret_key = "dev_key"


def parse_data(is_ajax=False):
    """
    Get the data from a specific mongodb, and parse in this struct:
    { new: dict {
        'date': string datetime,
        'source': string IP,
        'source_port': string port/protocol,
        'destiny': string IP,
        'destiny_port': string port/protocol
        }
    }
    Also parse if an ajax call is received.
    """
    full_rows = db.full_rows.find()
    if is_ajax:
        div = ""

    max_package = 50 #max quantity of scanned package to send
    for p in full_rows:
        post_id = p.get('_id')
        pack = p['not_parsed'].split()
        type_pack = pack[0]
        data = pack[1:len(pack)-1]

        temp = data[1].split('.')
        s_ip = ".".join(temp[0:len(temp)-1])
        s_port = temp[len(temp)-1]

        temp = data[3].split('.')
        d_ip = ".".join(temp[0:len(temp)-1])
        d_port = temp[len(temp)-1]

        new = {
                "date": type_pack,
                "source": s_ip,
                "source_port": s_port,
                "destiny": d_ip,
                "destiny_port": d_port
                }
        if is_ajax:
            div += "<tr class='warning'><td>{0}</td>".format(type_pack)
            div += "<td>{0}</td>".format(s_ip)
            div += "<td>{0}</td>".format(s_port)
            div += "<td>{0}</td>".format(d_ip)
            div += "<td>{0}</td></tr>".format(d_port)
        db.data_packs.insert_one(new)
        db.full_rows.delete_one({'_id':post_id})
        if is_ajax and max_package == 0:
            return div
        max_package -= 1

    if is_ajax:
        return div


def get_stats():
    pipeline = [
                {"$group":{"_id":"$source_port", "count":{"$sum":1}}},
                {"$sort": SON([("count", -1), ("_id", -1)])}
                ]
    quantity = list(db.data_packs.aggregate(pipeline))
    div = "<table id='stat-table' class='table table-striped'>\
            <tr>\
            <th>Puerto (protocolo)</th>\
            <th>Total de paquetes</th>\
            </tr><tbody>"
    for q in quantity:
        div += "<tr class='info'><td>{0}</td>".format(q['_id'])
        div += "<td>{0}</td></tr>".format(q['count'])
    div += "</tbody></table>"
    return div


@app.route('/remove/')
def remove():
    """
    Removes all data from databases.
    """
    db.data_packs.remove()
    db.full_rows.remove()
    return flask.redirect(flask.url_for('index'))


@app.route('/tcp_update/', methods=['POST'])
def update_tcp():
    return flask.jsonify({'data': parse_data(True),
                            'total': db.data_packs.find().count(),
                            'stats': get_stats()})


@app.route('/')
def index():
    if 'tcp_bool' not in flask.session:
        flask.session['tcp_bool'] = False
    data_packs = db.data_packs
    total = data_packs.find().count()

    page, per_page, offset = get_page_items()
    data = data_packs.find().skip(offset).\
                limit(per_page).sort('date', pymongo.DESCENDING)
    pipeline = [
                {"$group":{"_id":"$source_port", "count":{"$sum":1}}},
                {"$sort": SON([("count", -1), ("_id", -1)])}
                ]
    quantity = db.data_packs.aggregate(pipeline)
    pagination = get_pagination(page=page,
                                per_page=per_page,
                                total=total,
                                record_name=data)
    return flask.render_template("index.html",
                                    data_packs=data,
                                    page=page,
                                    per_page=per_page,
                                    total=total,
                                    quantity=quantity,
                                    pagination=pagination,)


def get_css_framework():
    return flask.current_app.config.get('CSS_FRAMEWORK', 'bootstrap3')


def get_link_size():
    return flask.current_app.config.get('LINK_SIZE', 'sm')


def show_single_page_or_not():
    return flask.current_app.config.get('SHOW_SINGLE_PAGE', False)


def get_page_items():
    page = int(flask.request.args.get('page', 1))
    per_page = flask.request.args.get('per_page')
    if not per_page:
        per_page = flask.current_app.config.get('PER_PAGE', 100)
    else:
        per_page = int(per_page)

    offset = (page - 1) * per_page
    return page, per_page, offset


def get_pagination(**kwargs):
    kwargs.setdefault('record_name', 'records')
    return Pagination(css_framework=get_css_framework(),
                        link_size=get_link_size(),
                        show_single_page=show_single_page_or_not(),
                        **kwargs
                        )


if __name__ == "__main__":
    #start_tcp().delay()
    #parse_data().delay()
    app.run(debug=True)
