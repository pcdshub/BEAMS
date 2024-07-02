from subprocess import Popen
import time

import py_trees
from epics import caget

from beams.tree_generator.TreeGenerator import TreeGenerator
from beams.tree_generator.TreeSerializer import CheckAndDoNodeEntry, CheckAndDoNodeType, CheckAndDoNodeTypeMode, CheckEntry, DoEntry


class TestTreeGenerator():
  def test_tree_obj_ser(self):
    fname = "tests/artifacts/eggs.json"
    tg = TreeGenerator(fname, CheckAndDoNodeEntry)

    ce = CheckEntry(Pv="PERC:COMP", Thresh=100)
    de = DoEntry(Pv="PERC:COMP", Mode=CheckAndDoNodeTypeMode.INC, Value=10)
    eg = CheckAndDoNodeEntry(name="self_test", check_and_do_type=CheckAndDoNodeType.CHECKPV, check_entry=ce, do_entry=de)

    assert tg.tree_spec == eg

  def test_tree_obj_execution(self):
    fname = "tests/artifacts/eggs.json"
    tg = TreeGenerator(fname, CheckAndDoNodeEntry)

    # start mock IOC # NOTE: assumes test is being run from top level of
    ioc_proc = Popen(["python3", "tests/mock_iocs/SelfTestIOC.py"])
    
    tree = tg.get_tree_from_config()

    while (tree.root.status != py_trees.common.Status.SUCCESS and tree.root.status != py_trees.common.Status.FAILURE): 
      for n in tree.root.tick():
        print(f"ticking: {n}")
        time.sleep(0.05)
        print(f"status of tick: {n.status}")

    rel_val = caget("PERC:COMP")
    assert rel_val >= 100

    ioc_proc.kill()
