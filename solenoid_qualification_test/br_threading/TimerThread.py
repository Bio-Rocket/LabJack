

import threading

class TimerThread(threading.Thread):
    def __init__(self, target, delay: float, event = None):
        threading.Thread.__init__(self, daemon=True)
        self.target = target
        self.delay = delay
        if event is None:
            self.stopped = threading.Event()
        else:
            self.stopped = event

    def run(self):
        while not self.stopped.wait(self.delay):
            self.target()
            # call a function