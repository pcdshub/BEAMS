from typing import Any, Dict
from uuid import UUID

import pytest

from beams.service.rpc_handler import TreeIdKey


@pytest.mark.parametrize("comparison, is_match,", [
    ("my rather long name", True),
    ("my rather ", False),
    (UUID("435f6dd5-0b2e-41c4-b07e-479a83271680"), True),
    (UUID("435f6dd5-0b2e-41c4-b07e-aaaaaaaaaaaa"), False),
    ("435f6dd", True),
])
def test_treeidkey_equality(comparison: Any, is_match: bool):
    tree_key = TreeIdKey(name="my rather long name",
                         uuid=UUID("435f6dd5-0b2e-41c4-b07e-479a83271680"))
    assert (tree_key == comparison) is is_match


@pytest.fixture
def tree_dict() -> Dict[TreeIdKey, int]:
    return {
        TreeIdKey(name="tree1",
                  uuid=UUID("9218d74e-b6c5-4fa3-8249-4ac45abc09fb")): 1,
        TreeIdKey(name="tree1",
                  uuid=UUID("50c82a04-7ce6-4656-bf2d-e26b08d8addf")): 2,
        TreeIdKey(name="tree3",
                  uuid=UUID("94b74b64-ad96-41dd-8489-1162032804a8")): 3,
    }


@pytest.mark.parametrize("key, expected_value", [
    (TreeIdKey(name="tree1", uuid=UUID("9218d74e-b6c5-4fa3-8249-4ac45abc09fb")), 1),
    (TreeIdKey(name="tree1", uuid=UUID("50c82a04-7ce6-4656-bf2d-e26b08d8addf")), 2),
    (TreeIdKey(name="tree3", uuid=UUID("94b74b64-ad96-41dd-8489-1162032804a8")), 3),
    (UUID("9218d74e-b6c5-4fa3-8249-4ac45abc09fb"), 1),
    # dict checks hash of object before equality, and don't consider name
    (UUID("50c82a04-7ce6-4656-bf2d-e26b08d8addf"), 2),
    (TreeIdKey(name="notmynname", uuid=UUID("9218d74e-b6c5-4fa3-8249-4ac45abc09fb")), 1),
    (UUID("94b74b64-ad96-41dd-8489-1162032804a8"), 3),
    ("tree1", None),  # hashes in dict are with uuid
    ("9218d74", None),
])
def test_treeidkey_getitem(
    tree_dict: Dict[TreeIdKey, int],
    key: TreeIdKey,
    expected_value: int
):
    if expected_value is None:
        with pytest.raises(KeyError):
            tree_dict[key]

        assert tree_dict.get(key) is None
    else:
        assert tree_dict[key] == expected_value
        assert tree_dict.get(key) == expected_value
