from bilibili import BiliSession

import ffmpeg
from flask import Flask, render_template, Response, session, send_file, request, redirect
from flask_caching import Cache
import oss2

import os
import time
from queue import Queue
from functools import partial
from threading import Thread, Lock
from warnings import warn

from .event import get_event_source, get_queue, Event
from .download import download_dash
from .storage import Storage

app = Flask(__name__)
app.config.update({
    'SECRET_KEY': os.getenv('SECRET_KEY') or os.urandom(16),
    'SESSDATA': os.getenv('BILI_SESSDATA'),
    'CACHE_TYPE': 'FileSystemCache',
    'CACHE_DIR': os.path.join(os.getenv('BILI_WORKDIR') or '.', 'cache'),
    'STORAGE_TYPE': os.getenv('STORAGE_TYPE') or 'local',
})

cache = Cache(app)
storage = Storage(app)


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


def handle_download(bvid, part, output_path):
    ses = BiliSession(app.config['SESSDATA'])
    queue = get_queue(session['id'])
    if not (video := cache.get(bvid)):
        cache.set(bvid, video := ses.get_video_meta(bvid))
    if part not in video['parts']:
        return False, 'no such part'
    last, current, total = '0.00', {}, 0
    part_meta = video['parts'][part]
    lock = Lock()

    def callback(percentage, t):
        nonlocal last, current, part
        with lock:
            current[t] = percentage
        progress = format(sum(current.values()) * 50, '.2f')
        if progress != last:
            queue.put(Event(f'process-{part}', progress))
            last = progress

    if not (quality := request.args.get('quality', None)):
        quality = max(part_meta['qualities']['meta']['accept_quality'])
    stream_meta = part_meta['qualities'][quality]['stream']
    if 'dash' in stream_meta:
        workdir = os.path.join(os.getenv('BILI_WORKDIR'), f'{bvid}-{part}')
        download_dash(workdir, output_path, partial(ses.get_stream, bvid=bvid), {
            i: stream_meta['dash'][i][0]['base_url']
            for i in ('video', 'audio')
        }, callback)
        if float(last) < 99.99:
            warn(f'{bvid}-{part}.mp4 maybe incomplete, {last}')
        return True, 'ok'
    else:
        return False, 'unsupported'


@app.route('/video/<string:bvid>/download/<int:part>')
def download(bvid, part):
    if 'id' not in session:
        session['id'] = os.urandom(16)

    queue = get_queue(session['id'])
    last = '0.00'

    def progress(current, total):
        nonlocal last
        if last != (last := format(current / total * 100, '.2f')):
            queue.put(Event(f'upload-{part}', last))

    output_path = os.path.join(os.getenv('BILI_WORKDIR'), f'{bvid}-{part}.mp4')
    if not storage.exists(f'{bvid}-{part}.mp4'):
        if not os.path.exists(output_path):
            res, msg = handle_download(bvid, part, output_path)
            if not res:
                return msg, 403
        storage.put(f'{bvid}-{part}.mp4', output_path, progress)
    # force redirect
    queue.put(Event(f'process-{part}', '100.00'))
    queue.put(Event(f'upload-{part}', '100.00'))
    return 'ok'


@app.route('/video/<string:bvid>/retrieve/<int:part>')
def retrieve(bvid, part):
    if storage.exists(f'{bvid}-{part}.mp4'):
        return redirect(storage.access(f'{bvid}-{part}.mp4'))
    else:
        return 'Not Found', 404


@app.route('/progress')
def progress():
    if 'id' not in session:
        session['id'] = os.urandom(16)
    return Response(
        get_event_source(session['id']),
        mimetype='text/event-stream'
    )
