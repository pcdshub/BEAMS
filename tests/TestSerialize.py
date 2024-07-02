import json
from apischema import serialize, deserialize
from beams.tree_generator.TreeSerializer \
  import CheckEntry, DoEntry, CheckAndDoNodeEntry, CheckAndDoNodeType, CheckAndDoNodeTypeMode


class TestSerializer:
  def test_serialize_basic(self):
    # c_obj = load_config("config.json")
    ce = CheckEntry(Pv="PERC:COMP", Thresh=100)
    de = DoEntry(Pv="PERC:COMP", Mode=CheckAndDoNodeTypeMode.INC, Value=10)
    eg = CheckAndDoNodeEntry(name="self_test", check_and_do_type=CheckAndDoNodeType.CHECKPV, check_entry=ce, do_entry=de)
    
    ser = serialize(CheckAndDoNodeEntry, eg)
    
    fname = "tests/artifacts/eggs.json"

    with open(fname, 'w') as fd:
      json.dump(ser, fd, indent=2)

    with open(fname, 'r') as fd:
      deser = json.load(fd)

    eg2 = deserialize(CheckAndDoNodeEntry, deser)
    assert eg2 == eg

  def test_serialize_youre_a_father_now(self):
    # c_obj = load_config("config.json")
    ce = CheckEntry(Pv="PERC:COMP", Thresh=100)
    de = DoEntry(Pv="PERC:COMP", Mode=CheckAndDoNodeTypeMode.INC, Value=10)
    eg = CheckAndDoNodeEntry(name="self_test", check_and_do_type=CheckAndDoNodeType.CHECKPV, check_entry=ce, do_entry=de)
    
    ser = serialize(CheckAndDoNodeEntry, eg)
    
    fname = "tests/artifacts/eggs2.json"

    with open(fname, 'w') as fd:
      json.dump(ser, fd, indent=2)

    with open(fname, 'r') as fd:
      deser = json.load(fd)

    eg2 = deserialize(CheckAndDoNodeEntry, deser)
    assert eg2 == eg