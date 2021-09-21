import threading
import time


class RepeatedTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer = None
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.is_running = False
        self.next_call = time.time()
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self.next_call += self.interval
            self._timer = threading.Timer(self.next_call - time.time(), self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False


def format_time(time: int) -> str:
    """
    Formats time (in seconds) to a string with time in weeks / days / hours / minutes / seconds
    """
    formatted_string = []

    seconds = time % 60
    if seconds > 0:
        formatted_string.append(f"{seconds} second{'s' * (seconds > 1)}")

    time //= 60
    minutes = time % 60
    if minutes > 0:
        formatted_string.append(f"{minutes} minute{'s' * (minutes > 1)}")

    time //= 60
    hours = time % 60
    if hours > 0:
        formatted_string.append(f"{hours} hour{'s' * (hours > 1)}")

    time //= 60
    days = time % 24
    if days > 0:
        formatted_string.append(f"{days} day{'s' * (days > 1)}")

    time //= 24
    weeks = time % 7
    if weeks > 0:
        formatted_string.append(f"{weeks} week{'s' * (weeks > 1)}")

    return ", ".join(formatted_string[::-1])
