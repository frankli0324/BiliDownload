import os


class BaseBackend:
    def get_config(self, item, default=None):
        return self.app.config.get(item, os.getenv(item)) or default

    def put(self, obj_name, obj_local, progress_callback=None):
        # override these for logging
        pass

    def get(self, obj_name):
        pass

    def access(self, obj_name):
        pass

    def __init__(self, app):
        self.app = app
