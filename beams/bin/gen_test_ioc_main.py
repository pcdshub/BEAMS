import json
from pathlib import Path
from typing import Iterator

import jinja2


def main(
    filepath: str,
):
    with open(filepath, "r") as fd:
        deser = json.load(fd)
    all_pvnames = sorted(list(set(pv for pv in walk_dict_pvs(deser))))

    if not all_pvnames:
        raise RuntimeError(f"Found zero PVs in {filepath}")

    jinja_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(Path(__file__).parent),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = jinja_env.get_template("test_ioc.py.j2")
    rendered = template.render(all_pvnames=all_pvnames)
    print(rendered)


def walk_dict_pvs(tree_dict: dict) -> Iterator[str]:
    for key, value in tree_dict.items():
        if key == "pv" or key == "pv_name" and value:
            yield str(value)
        elif isinstance(value, dict):
            yield from walk_dict_pvs(value)
        elif isinstance(value, list):
            for subitem in value:
                # Don't try to handle nested lists etc.
                if isinstance(subitem, dict):
                    yield from walk_dict_pvs(subitem)
