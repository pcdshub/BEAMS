from beams.sequencer.helpers.Worker import Worker
from multiprocessing import Value


class TestTask:
  def test_obj_instantiation(self):
    class WorkChild(Worker):
      def __init__(self):
        super().__init__("test_worker")
        self.value = Value('d', 0)

      def work_func(self):
        while (self.do_work.value or self.value.value < 100):
          self.value.value += 10

    w = WorkChild()
    w.start_work()
    w.stop_work()  # blocking calls join

    assert w.value.value == 100

  def test_class_member_instantiation(self):
    a = Worker("test_worker")
    val = Value('i', 10)
    
    def work_func(self):
      while (self.do_work.value or val.value < 100):
        val.value += 10
    a.set_work_func(work_func)

    a.start_work()
    a.stop_work()
    assert val.value == 100

  def test_inline_instantation(self):
    val = Value('i', 10)

    def work_func(self):
      while (self.do_work.value or val.value < 100):
        val.value += 10
    a = Worker("test_worker", work_func=work_func)
    a.start_work()
    a.stop_work()
    assert val.value == 100
