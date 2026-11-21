"""Testable, dependency-free shuffle queue and monotonic interval scheduler."""
import random
import time

class ShuffleQueue:
    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        self.items = []
        self.pending = []
        self.last = None
        self.shuffle = True
        self.count = 0

    def load(self, items):
        self.items = list(dict.fromkeys(items))
        self.pending = []
        self.last = None
        self.count = 0

    def next(self):
        if not self.items:
            return None
        if not self.pending:
            self.pending = list(self.items)
            if self.shuffle:
                self.rng.shuffle(self.pending)
            if len(self.pending) > 1 and self.pending[0] == self.last:
                self.pending[0], self.pending[-1] = self.pending[-1], self.pending[0]
        item = self.pending.pop(0)
        self.last = item
        self.count += 1
        return item

class IntervalClock:
    def __init__(self):
        self.interval = 60
        self.deadline = None
        self.running = False

    def start(self, seconds):
        self.interval = max(1, float(seconds))
        self.deadline = time.monotonic() + self.interval
        self.running = True

    def stop(self):
        self.running = False
        self.deadline = None

    def due(self):
        if self.running and time.monotonic() >= self.deadline:
            self.deadline = time.monotonic() + self.interval
            return True
        return False
