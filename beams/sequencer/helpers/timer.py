import time


class Timer():
    def __init__(self,
                 name: str,
                 timer_period_seconds: float,
                 auto_start: bool = False,
                 is_periodic: bool = False):
        self.name = name
        self.timer_period_seconds = timer_period_seconds
        self.is_periodic = is_periodic
        self.auto_start = auto_start
        if (self.auto_start):
            self.timer_start_time = time.monotonic()
        else:
            self.timer_start_time = -1

    def start_timer(self) -> None:
        self.timer_start_time = time.time()

    def check_valid_timer(self) -> bool:
        if (self.timer_start_time == -1):
            raise RuntimeError(f"{self.name} timer checked but not started")

    def is_elapsed(self) -> bool:
        elapsed = self.get_elapsed()
        if (elapsed > self.timer_period_seconds):
            if (self.is_periodic):
                self.timer_start_time = time.time()
            return True
        else:
          return False

    def get_elapsed(self) -> float:
        self.check_valid_timer()
        now = time.time()
        return now - self.timer_start_time
