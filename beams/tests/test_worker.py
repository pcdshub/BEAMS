import time
from multiprocessing import Value
from beams.sequencer.helpers.Worker import Worker


class TestTask:
    def test_obj_instantiation(self):
        class CoolWorker(Worker):
            def __init__(self,
                         proc_name: str,
                         work_func):
                super().__init__(proc_name=proc_name,
                                 work_func=work_func,
                                 add_args=())
                self.val = Value('i', 0)

        def work_func(self):
            while self.do_work.value or self.val.value < 100:
                if self.val.value < 100:  # Note: value captured via closure
                    time.sleep(0.01)
                    with self.val.get_lock():
                        self.val.value += 10  # Note: value captured via closure

        c = CoolWorker("cool_guy",
                       work_func=work_func)
        c.start_work()
        time.sleep(1)  # Note: need actual time for the thing to happen
        c.stop_work()
        with c.val.get_lock():
            assert c.val.value == 100

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
                time.sleep(0.01)
                with val.get_lock():
                    if val.value < 100:  # Note: value captured via closure
                        val.value += 10

        a = Worker("test_worker", work_func=work_func)
        a.start_work()
        time.sleep(1)
        a.stop_work()
        assert val.value == 100
