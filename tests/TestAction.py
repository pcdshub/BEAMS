class TestTask:
  def test_task_state_cycle(self):
    assert True

  def test_two(self):
    # While I have no love for meaningless commited code
    # Let this serve as an ugly reminder to actually enable these Tasks to communicate between
    # One another and to unit test that functionality here
    self.value = 2
    assert self.value == 2
