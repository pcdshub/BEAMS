from beams.sequencer.remote_calls.sequencer_pb2 import GenericMessage

from apischema import deserialize
import json


def GenerateTreeFromRequest(request: GenericMessage):
  pass


class TreeGenerator():
  def __init__(self, config_fname, node_type):
    with open(config_fname, "r+") as fd:
      self.tree_spec = deserialize(node_type, json.load(fd))

  def get_tree_from_config(self):
    # check if requested sequence name is in entries
    return self.tree_spec.get_tree()
