import time
from multiprocessing import Value

from beams.sequencer.helpers.Worker import Worker


class TestTask:
    def test_obj_instantiation(self):
        class WorkChild(Worker):
            def __init__(self):
                super().__init__("test_worker")
                self.value = Value("d", 0)  # Note: here value is a member object

            def work_func(self):
                while self.do_work.value or self.value.value < 100:
                    if self.value.value < 100:  # Note: here we reference member object
                        self.value.value += 10

        w = WorkChild()
        w.start_work()
        w.stop_work()  # blocking calls join

        assert w.value.value == 100

    def test_class_member_instantiation(self):
        a = Worker("test_worker")
        val = Value("i", 10)  # Note: value declared here to be captured via closure

        def work_func(self):
            while self.do_work.value or val.value < 100:
                if val.value < 100:  # Note: value captured via closure
                    val.value += 10  # Note: value captured via closure

        a.set_work_func(work_func)

        a.start_work()
        time.sleep(1)
        a.stop_work()
        assert val.value == 100

    def test_inline_instantation(self):
        val = Value("i", 10)

        def work_func(self):
            while self.do_work.value or val.value < 100:
                if val.value < 100:  # Note: value captured via closure
                    val.value += 10

        a = Worker("test_worker", work_func=work_func)
        a.start_work()
        a.stop_work()
        assert val.value == 100
