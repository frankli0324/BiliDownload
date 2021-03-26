from werkzeug.utils import secure_filename
from werkzeug.urls import url_join

from .base import BaseBackend

import os
from warnings import warn


class LocalBackend(BaseBackend):
    def __init__(self, app):
        super().__init__(app)
        self.base_dir = self.get_config('LOCAL_BASEDIR', '/var/lib/flask_storage')
        self.base_url = self.get_config('LOCAL_BASEURL', '/static/')

    def exists(self, obj_name):
        obj_name = secure_filename(obj_name)
        if not obj_name:
            warn('unsafe object name')
            return True
        return os.path.exists(os.path.join(self.base_dir, obj_name))

    def put(self, obj_name, obj_local, progress_callback=None):
        obj_name = secure_filename(obj_name)
        if not self.exists(obj_name):
            os.rename(obj_local, os.path.join(self.base_dir, obj_name))
        else:
            warn('target exists, no action performed')
        if progress_callback:
            progress_callback(1, 1)

    def get(self, obj_name):
        obj_name = secure_filename(obj_name)
        if not obj_name or not self.exists(obj_name):
            return
        return open(os.path.join(self.base_dir, obj_name))

    def access(self, obj_name):
        obj_name = secure_filename(obj_name)
        return url_join(self.base_url, obj_name)
