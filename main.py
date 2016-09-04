# -*- coding: utf-8 -*-
import pymongo
import flask
from flask.ext.paginate import Pagination
from bson.code import Code
from tcpdump import tcpdaemon

client = pymongo.MongoClient()
db = client['tcp_python']

app = flask.Flask(__name__)
app.secret_key = "dev_key"

@app.route('/remove/')
def remove():
    db.posts.remove()
    return flask.redirect(flask.url_for('index'))


@app.route('/tcpdump/', methods=['POST'])
def update_tcp:
    if request.method == 'POST':
        pass
    return False


@app.route('/')
def index():
    posts = db.posts
    total = posts.find().count()

    page, per_page, offset = get_page_items()
    data = posts.find().skip(offset).limit(per_page).sort('date', pymongo.DESCENDING)

    pipeline = [{"$group":{"_id":"$source_port", "count":{"$sum":1}}}]
    quantity = db.collection.aggregate(pipeline)
    #print quantity
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
    app.run(debug=True)
