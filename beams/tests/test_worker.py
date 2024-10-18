import time
from multiprocessing import Value

from beams.sequencer.helpers.Worker import Worker


class TestTask:
    def test_obj_instantiation(self):
        class CoolWorker(Worker):
            def __init__(self, proc_name: str):
                super().__init__(proc_name=proc_name)
                self.val = Value('i', 0)

            def work_func(self):
                while self.do_work.value or self.val.value < 100:
                    if self.val.value < 100:
                        # Note: even in python if a full bore loop captures a
                        # lock other Processes may not have time to acquire this
                        # shared resource; therefore the sleep is very strongly
                        # suggested if not needed when using a lock
                        time.sleep(0.01)
                        with self.val.get_lock():
                            self.val.value += 10  # Note: value captured via closure

        c = CoolWorker(proc_name="cool_guy")
        c.start_work()
        time.sleep(1)  # Note: need actual time for the thing to happen
        c.stop_work()
        with c.val.get_lock():
            assert c.val.value == 100

    def test_inline_instantation(self):
        val = Value("i", 10)

        def work_func(do_work):
            while (do_work.value):
                time.sleep(0.1)
                while val.value < 100:
                    time.sleep(0.01)
                    with val.get_lock():
                        if val.value < 100:  # Note: value captured via closure
                            val.value += 10

        a = Worker("test_worker", work_func=work_func)
        a.start_work()
        time.sleep(1)
        a.stop_work()
        assert val.value == 100
