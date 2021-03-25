from bilibili.utils import download_progress

import os
from functools import partial
from threading import Thread

import ffmpeg


def start_stream_downlaod(get_stream, url, dest, update):
    stream_len, stream = get_stream(url=url)
    thread = Thread(
        target=download_progress,
        args=(stream_len, stream, dest, update)
    )
    thread.start()
    return thread


def download_dash(workdir, output_path, get_stream, url, callback=None):
    os.makedirs(workdir, exist_ok=True)
    for thread in [
        start_stream_downlaod(
            get_stream, url[i],
            os.path.join(workdir, i + '_track'),
            partial(callback, t=i)
        )
        for i in ('audio', 'video')
    ]:
        thread.join()
    audio = ffmpeg.input(os.path.join(workdir, 'audio_track'))
    video = ffmpeg.input(os.path.join(workdir, 'video_track'))
    out = ffmpeg.output(
        video, audio, output_path,
        vcodec="copy", acodec="copy",
        strict='experimental')
    out.global_args('-loglevel', 'warning', '-stats').run()
