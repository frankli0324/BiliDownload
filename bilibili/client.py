from os import path
import functools
import shutil

from requests import Session

from .utils import LazyDict


class BiliSession(Session):
    def __init__(self, sess):
        super().__init__()
        with open(path.join(path.dirname(__file__), 'ua')) as f:
            self.headers.update({'User-Agent': f.read()})
        self.cookies.set('SESSDATA', sess)

    def request(self, method, url, *args, **kwargs):
        if url.startswith('/'):
            url = 'https://api.bilibili.com' + url
            json = super().request(method, url, *args, **kwargs).json()
            assert json['code'] == 0
            return json['data']
        else:
            return super().request(method, url, *args, **kwargs)

    @property
    def user_profile(self):
        return self.get('/nav')

    def get_video_meta(self, bvid):
        video = self.get('/x/web-interface/view', params={'bvid': bvid})
        meta = {'meta': video, 'parts': {}, 'bvid': bvid}
        for part in video['pages']:
            meta['parts'][part['page']] = LazyDict()
            part_meta = meta['parts'][part['page']]
            part_meta['meta'] = part
            part_meta['cid'] = part['cid']
            part_meta['qualities'] = (self.get_qualities, bvid, part['cid'])
        return meta

    def get_qualities(self, bvid, cid):
        qualities = {}
        qualities['meta'] = self.get('/x/player/playurl', params={
            'bvid': bvid, 'cid': cid, 'fourk': 1
        })
        for quality in qualities['meta']['support_formats']:
            qualities[quality['quality']] = LazyDict(quality)
            qualities[quality['quality']]['stream'] = (
                self.get_stream_url, bvid, cid, quality['quality']
            )
        return qualities

    def get_stream_url(self, bvid, cid, quality):
        return self.get('/x/player/playurl', params={
            'bvid': bvid, 'cid': cid, 'fourk': 1,
            'fnval': 16, 'qn': quality
        })

    def get_stream(self, bvid, url):
        self.headers.update({
            'Referer': 'https://www.bilibili.com/video/' + bvid
        })
        response = self.get(url, stream=True)
        self.headers.pop('Referer')
        # response.raw.read = functools.partial(response.raw.read, decode_content=True)
        # with open(file, 'wb') as file:
        #     shutil.copyfileobj(response.raw, file, length=total_bytes)
        total_bytes = int(response.headers.get('content-length', 0))
        return total_bytes, response.iter_content
