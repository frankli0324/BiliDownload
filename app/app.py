from bilibili import BiliSession

import ffmpeg
from flask import Flask, render_template, Response, session, send_file, request
from flask_caching import Cache

import os
import time
from queue import Queue
from functools import partial
from threading import Thread

from .event import get_event_source, get_queue, Event
from .download import download_dash

app = Flask(__name__)
app.config['SESSDATA'] = os.getenv('BILI_SESSDATA')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') or os.urandom(16)
app.config['CACHE_TYPE'] = 'FileSystemCache'
app.config['CACHE_DIR'] = os.path.join(os.getenv('BILI_WORKDIR') or '.', 'cache')
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


@app.route('/video/<string:bvid>/download/<int:part>')
def download(bvid, part):
    if 'id' not in session:
        session['id'] = os.urandom(16)
    ses = BiliSession(app.config['SESSDATA'])
    queue = get_queue(session['id'])
    if not (video := cache.get(bvid)):
        cache.set(bvid, video := ses.get_video_meta(bvid))
    last = '0.00'
    current = {}
    total = 0

    def callback(percentage, t):
        nonlocal last, part
        current[t] = percentage
        progress = format(sum(current.values()) * 50, '.2f')
        if progress != last:
            queue.put(Event(f'progress-{part}', progress))
            last = progress
    output_path = os.path.join(os.getenv('BILI_OUTDIR'), f'{bvid}-{part}.mp4')
    if not os.path.exists(output_path):
        part_meta = video['parts'][part]
        if not (quality := request.args.get('quality', None)):
            quality = max(part_meta['qualities']['meta']['accept_quality'])
        stream_meta = part_meta['qualities'][quality]['stream']
        if 'dash' in stream_meta:
            workdir = os.path.join(os.getenv('BILI_WORKDIR'), f'{bvid}-{part}')
            download_dash(workdir, output_path, partial(ses.get_stream, bvid=bvid), {
                i: stream_meta['dash'][i][0]['base_url']
                for i in ('video', 'audio')
            }, callback)
        else:
            return 'unsupported'
    else:
        queue.put(Event(f'progress-{part}', '100.00'))
    return 'ok'


@app.route('/video/<string:bvid>/retrieve/<int:part>')
def retrieve(bvid, part):
    output_path = os.path.join(os.getenv('BILI_OUTDIR'), f'{bvid}-{part}.mp4')
    return send_file(output_path, as_attachment=True)


@app.route('/progress')
def progress():
    if 'id' not in session:
        session['id'] = os.urandom(16)
    return Response(
        get_event_source(session['id']),
        mimetype='text/event-stream'
    )
