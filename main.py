# -*- coding: utf-8 -*-
import pymongo
import os
import flask
import flask_sijax
import subprocess as sub
from flask_paginate import Pagination
from bson.son import SON

client = pymongo.MongoClient()
db = client['tcp_python']
path = os.path.join('.', os.path.dirname(__file__), 'static/js/sijax/')
app = flask.Flask(__name__)
app.config['SIJAX_STATIC_PATH'] = path
app.config['SIJAX_JSON_URI'] = '/static/js/sijax/json2.js'
flask_sijax.Sijax(app)
app.secret_key = "dev_key"


def parse_data():
    profiles = db.profiles.find()

    for p in profiles:
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
                "destiny": d_ip,
                "source_port": s_port,
                "destiny_port": d_port
                }
        db.posts.insert_one(new)
        db.profiles.delete_one({'_id':post_id})


@flask_sijax.route(app, '/hello')
def hello():
    # Every Sijax handler function (like this one) receives at least
    # one parameter automatically, much like Python passes `self`
    # to object methods.
    # The `obj_response` parameter is the function's way of talking
    # back to the browser
    def say_hi(obj_response):
        obj_response.alert('Hi there!')

    if flask.g.sijax.is_sijax_request:
        # Sijax request detected - let Sijax handle it
        flask.g.sijax.register_callback('say_hi', say_hi)
        return flask.g.sijax.process_request()

    # Regular (non-Sijax request) - render the page template
    return _render_template()


@app.route('/remove/')
def remove():
    db.posts.remove()
    db.profiles.remove()
    return flask.redirect(flask.url_for('index'))


@app.route('/tcpdump/', methods=['POST'])
def update_tcp():

    return False


@app.route('/')
def index():
    if 'tcp_bool' not in flask.session:
        flask.session['tcp_bool'] = False
    posts = db.posts
    total = posts.find().count()

    page, per_page, offset = get_page_items()
    data = posts.find().skip(offset).limit(per_page).sort('date', pymongo.DESCENDING)

    pipeline = [
                {"$group":{"_id":"$source_port", "count":{"$sum":1}}},
                {"$sort": SON([("count", -1), ("_id", -1)])}
                ]
    quantity = db.posts.aggregate(pipeline)
    pagination = get_pagination(page=page,
                                per_page=per_page,
                                total=total,
                                record_name=data)
    return flask.render_template("index.html",
                                    posts=data,
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
