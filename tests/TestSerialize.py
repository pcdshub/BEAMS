import json
from apischema import serialize, deserialize
from beams.tree_generator.TreeSerializer \
  import CheckEntry, DoEntry, CheckAndDoNodeEntry, CheckAndDoNodeType, CheckAndDoNodeTypeMode, TreeSpec


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
    """
    Build children check and dos
    """
    # insert reticule if ret is not found
    ce1 = CheckEntry(Pv="RET:FOUND", Thresh=1)  # TODO: should make a check / set mode
    de1 = DoEntry(Pv="RET:FOUND", Mode=CheckAndDoNodeTypeMode.SET, Value=1)
    # de = DoEntry(Pv="RET:SET", Mode=CheckAndDoNodeTypeMode.SET, Value=1)  # TODO: once we have better feel of caproto plumb this up in mock
    eg1 = CheckAndDoNodeEntry(name="ret_find", check_and_do_type=CheckAndDoNodeType.CHECKPV, check_entry=ce1, do_entry=de1)
    
    # acquire pixel to world frame transform
    ce2 = CheckEntry(Pv="RET:INSERT", Thresh=1)  # TODO: should make a check / set mode
    de2 = DoEntry(Pv="RET:INSERT", Mode=CheckAndDoNodeTypeMode.SET, Value=1)
    eg2 = CheckAndDoNodeEntry(name="ret_insert", check_and_do_type=CheckAndDoNodeType.CHECKPV, check_entry=ce2, do_entry=de2)

    eg_root = TreeSpec(name="fake_reticle", 
                       children=[eg1, eg2])
    
    fname = "tests/artifacts/eggs2.json"
    ser = serialize(TreeSpec, eg_root)
    with open(fname, 'w') as fd:
      json.dump(ser, fd, indent=2)

    with open(fname, 'r') as fd:
      deser = json.load(fd)

    eg_deser = deserialize(TreeSpec, deser)
    assert eg_root == eg_deser
