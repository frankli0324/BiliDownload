from .base import BaseBackend

import os


class AliossBackend(BaseBackend):
    # todo: error handling
    def __init__(self, app):
        import oss2
        super().__init__(app)
        if True and \
                (aid := self.get_config('ALI_ACCESSID')) and \
                (asrt := self.get_config('ALI_SECRET')) and \
                (endpoint := self.get_config('ALI_ENDPOINT')) and \
                (bucket := self.get_config('ALI_BUCKETID')):
            auth = oss2.Auth(aid, asrt)
            self.bucket = oss2.Bucket(auth, endpoint, bucket)
        else:
            raise RuntimeError('Alicloud OSS environments not set')

    def exists(self, obj_name):
        return self.bucket.object_exists(obj_name)

    def put(self, obj_name, obj_local, progress_callback=None):
        with open(obj_local, 'rb') as f:
            self.bucket.put_object(obj_name, f, progress_callback=progress_callback)

    def access(self, obj_name, expire=500):
        original = self.bucket._make_url.netloc
        self.bucket._make_url.netloc = original.replace('-internal', '')
        if not self.exists(obj_name):
            return
        url = self.bucket.sign_url('GET', obj_name, expire, params={
            'response-content-disposition': f'attachment; filename="{obj_name}"'
        })
        self.bucket._make_url.netloc = original
        return url