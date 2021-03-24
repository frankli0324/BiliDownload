import json
from queue import Queue, Empty


event_queues = {}


class Event:
    def __init__(self, event_type, data):
        self.type = event_type
        self.data = data

    def __str__(self):
        data = json.dumps(self.data) \
            if not isinstance(self.data, str)\
            else self.data

        return f'event:{self.type}\ndata:{data}\n\n'


def get_queue(sessid):
    if sessid not in event_queues:
        event_queues[sessid] = Queue()
    return event_queues[sessid]

def get_event_source(sessid):
    queue = get_queue(sessid)
    yield 'event:ping\ndata:1\n\n'
    while True:
        try:
            event = queue.get(timeout=5)
            assert isinstance(event, Event)
            yield str(event)
        except Empty:
            yield 'event:ping\ndata:1\n\n'
