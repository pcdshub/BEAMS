import py_trees
from epics import caput, caget
import time

from apischema import serialize, deserialize
import json

from beams.behavior_tree.ActionNode import ActionNode
from beams.behavior_tree.ConditionNode import ConditionNode
from beams.behavior_tree.CheckAndDo import CheckAndDo

from beams.sequencer.remote_calls.sequencer_pb2 import SequenceCommand, AlterState, GenericCommand, Empty
from beams.sequencer.remote_calls.sequencer_pb2 import SequenceType, RunStateType

from beams.tree_generator.TreeSerializer \
  import CheckEntry, DoEntry, CheckAndDoNodeEntry, CheckAndDoNodeType, CheckAndDoNodeTypeMode


class TreeGenerator():
  def __init__(self, config_fname, node_type):
    with open(config_fname, "r+") as fd:
      self.tree_spec = deserialize(node_type, json.load(fd))


def get_self_test_tree():
  """
  Needs procServ / caproto launched IOC to be tested against
  """
  percentage_complete_pv = "PERC:COMP"
  
  def update_pv(comp_condition, volatile_status, **kwargs):
    value = 0
    while not comp_condition(value):
      value = caget(percentage_complete_pv)
      if value >= 100:
        volatile_status.set_value(py_trees.common.Status.SUCCESS)
      py_trees.console.logdebug(f"Value is {value}, BT Status: {volatile_status.get_value()}")
      caput(percentage_complete_pv, value + 10)
      time.sleep(1)
  
  py_trees.logging.level = py_trees.logging.Level.DEBUG
  comp_cond = lambda x: x >= 100
  action = ActionNode("update_pv", update_pv, comp_cond)

  checky = lambda : caget(percentage_complete_pv) >= 100
  check = ConditionNode("check_pv", checky)

  candd = CheckAndDo("yuhh", check, action)
  candd.setup()

  return candd


def generate_tree_from_config(self, sequence_name):
  # check if requested sequence name is in entries
  self.tree_spec.get_tree()

  def work_func(comp_condition, update_value, work, volatile_status, **kwargs):
    # check arbitrary completion condition
    while not comp_condition(value):
      # update value which the completion condition is checked against
      value = update_value()
      py_trees.console.logdebug(f"Value is {value}, BT Status: {volatile_status.get_value()}")
      if comp_condition(value):
        volatile_status.set_value(py_trees.common.Status.SUCCESS)
        return
      work(value)
      time.sleep(1)
    return


def UnpackRequest(req: GenericCommand):
  m_type = req.WhichOneof("kind")
  if (m_type == "seq_m"):
    return req.seq_m.seq_t
  elif (m_type == "alt_m"):
    return req.alt_m.alt_t


# sequence_type_to_tree_dictionary = {
#   SequenceType.SAFE : None,
#   SequenceType.SELF_TEST : get_self_test_tree,
#   SequenceType.CHANGE_GMD_GAS : get_change_gmd_gas_tree
# }  


# def GenerateTreeFromRequest(request):
#   req = UnpackRequest(request)
#   print(f"you're looking at: {req}")
#   to_be_ticked = sequence_type_to_tree_dictionary[req]
#   # return to_be_ticked
