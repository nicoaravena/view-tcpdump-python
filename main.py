# -*- coding: utf-8 -*-
import pymongo
import flask
import subprocess as sub
from flask_paginate import Pagination
from celery import Celery
from bson.son import SON

client = pymongo.MongoClient()
db = client['tcp_python']

app = flask.Flask(__name__)
app.config.update(
CELERY_BROKER_URL='amqp://localhost:6379',
CELERY_RESULT_BACKEND='amqp://localhost:6379'
)
app.secret_key = "dev_key"


def make_celery(conf):
    celery = Celery(conf.import_name,
                    backend=conf.config['CELERY_RESULT_BACKEND'],
                    broker=conf.config['CELERY_BROKER_URL'])
    celery.conf.update(conf.config)
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with conf.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery


celery = make_celery(app)


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

        new = { "package" :
                    {
                    "date": type_pack,
                    "source": s_ip,
                    "destiny": d_ip,
                    "source_port": s_port,
                    "destiny_port": d_port,
                    }
                }
        db.posts.insert_one(new)
        db.profiles.delete_one({'_id':post_id})


@app.route('/stream_sqrt')
def stream():
    def generate():
        parse_data()

    return app.response_class(generate(), mimetype='text/plain')

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
    print quantity
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
