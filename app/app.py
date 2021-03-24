from bilibili import BiliSession

from flask import Flask, render_template, Response, session
from flask_caching import Cache

import os
import time
from queue import Queue

from .event import get_event_source

app = Flask(__name__)
app.config['SESSDATA'] = os.getenv('BILISESSDATA')
app.config['SECRET_KEY'] = 'aaa'
app.config['CACHE_TYPE'] = 'FileSystemCache'
app.config['CACHE_DIR'] = 'cache'
cache = Cache(app)


@app.template_filter('ctime')
def timectime(s):
    return time.ctime(s)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/frankli_setsession/<string:session>')
def sesset(session):
    app.config['SESSDATA'] = session
    return ''


@app.route('/video/<string:bvid>/')
def video(bvid):
    if 'id' not in session:
        session['id'] = os.urandom(16)
    if not (video := cache.get(bvid)):
        ses = BiliSession(app.config['SESSDATA'])
        cache.set(bvid, video := ses.get_video_meta(bvid))
    return render_template('video.html', video=video)


@app.route('/progress')
def progress():
    if 'id' not in session:
        session['id'] = os.urandom(16)
    return Response(
        get_event_source(session['id']),
        mimetype='text/event-stream'
    )
