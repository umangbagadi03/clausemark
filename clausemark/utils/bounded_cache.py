import threading
from collections import OrderedDict


class BoundedCache:
    """Remembers the most recently used items and forgets the oldest past the limit."""

    def __init__(self, max_items):
        self.max_items = max_items
        self.items = OrderedDict()
        self.lock = threading.Lock()

    def get(self, key):
        """Returns None when the key is not in the cache."""
        with self.lock:
            if key not in self.items:
                return None
            self.items.move_to_end(key)
            return self.items[key]

    def put(self, key, value):
        with self.lock:
            self.items[key] = value
            self.items.move_to_end(key)
            if len(self.items) > self.max_items:
                self.items.popitem(last=False)
