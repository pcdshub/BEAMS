from subprocess import Popen, TimeoutExpired
import time
import signal 
import sys

import py_trees
from epics import caget

from beams.tree_generator.TreeGenerator import TreeGenerator
from beams.tree_generator.TreeSerializer import CheckAndDoNodeEntry, CheckAndDoNodeTypeMode, CheckEntry, DoEntry, TreeSpec


class TestTreeGenerator():
  def test_tree_obj_ser(self):
    fname = "tests/artifacts/eggs.json"
    tg = TreeGenerator(fname, CheckAndDoNodeEntry)

    ce = CheckEntry(Pv="PERC:COMP", Thresh=100)
    de = DoEntry(Pv="PERC:COMP", Mode=CheckAndDoNodeTypeMode.INC, Value=10)
    eg = CheckAndDoNodeEntry(name="self_test", check_and_do_type=CheckAndDoNodeEntry.CheckAndDoNodeType.CHECKPV, check_entry=ce, do_entry=de)

    assert tg.tree_spec == eg

  # def test_tree_obj_execution(self):
  #   fname = "tests/artifacts/eggs.json"
  #   tg = TreeGenerator(fname, CheckAndDoNodeEntry)

  #   # start mock IOC # NOTE: assumes test is being run from top level of
  #   ioc_proc = Popen([sys.executable, "tests/mock_iocs/SelfTestIOC.py"])
    
  #   tree = tg.get_tree_from_config()

  #   while (tree.root.status != py_trees.common.Status.SUCCESS and tree.root.status != py_trees.common.Status.FAILURE): 
  #     for n in tree.root.tick():
  #       print(f"ticking: {n}")
  #       time.sleep(0.1)
  #       print(f"status of tick: {n.status}")

  #   rel_val = caget("PERC:COMP")
  #   assert rel_val >= 100

  #   ioc_proc.send_signal(signal.SIGINT)

  #   try:
  #       ioc_proc.wait(timeout=1)
  #   except TimeoutExpired:
  #       print('IOC did not exit in a timely fashion')
  #       ioc_proc.terminate()
  #       print('IOC terminated')
  #   else:
  #       print('IOC has exited')

  def test_father_tree_execution(self):
    ioc_proc = Popen([sys.executable, "tests/mock_iocs/ImagerNaysh.py"])
    time.sleep(1)

    fname = "tests/artifacts/eggs2.json"
    tg = TreeGenerator(fname, TreeSpec)
    tree = tg.get_tree_from_config()

    while (tree.root.status != py_trees.common.Status.SUCCESS and tree.root.status != py_trees.common.Status.FAILURE): 
      for n in tree.root.tick():
        print(f"ticking: {n}")
        time.sleep(0.1)
        print(f"status of tick: {n.status}")
    
    check_insert = caget("RET:INSERT")

    assert check_insert == 1

    ioc_proc.terminate()
