from .local import LocalBackend
from .alioss import AliossBackend

backends = {
    'local': LocalBackend,
    'alioss': AliossBackend,
}


class Storage:
    # unsafe, don't let others control obj_name!!
    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        st = app.config.get('STORAGE_TYPE', 'local')
        if st not in backends:
            raise RuntimeError('unsupported storage type')
        self.backend = backends[st](app)

    def __getattr__(self, name):
        if hasattr(self.backend, name):
            return getattr(self.backend, name)
        else:
            raise AttributeError()
