from __future__ import annotations

import json
import time
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Any, Iterable, Iterator

import jinja2
from caproto import ReadNotifyResponse
from caproto.threading.client import Batch, Context


@dataclass(frozen=True, eq=True, order=True)
class PVInfoForJ2:
    python_name: str
    pvname: str
    value: Any
    dtype: str
    enum_strings: list[str]
    precision: int

    @classmethod
    def from_result(cls: type[PVInfoForJ2], pvname: str, response: ReadNotifyResponse):
        try:
            enum_strings = response.metadata.enum_strings
        except AttributeError:
            enum_strings = []
        try:
            precision = response.metadata.precision
        except AttributeError:
            precision = 0
        return cls(
            python_name=pvname.lower().replace(":", "_").replace(".", "_"),
            pvname=pvname,
            value=response.data if response.data_count > 1 else response.data[0],
            dtype=response.data_type.name.removeprefix("CTRL_"),
            enum_strings=[bt.decode("utf8") for bt in enum_strings],
            precision=precision,
        )


def collect_pv_info(pvnames: Iterable[str]) -> list[PVInfoForJ2]:
    ctx = Context()
    pvs = ctx.get_pvs(*pvnames)
    results = []

    for pv in pvs:
        pv.wait_for_connection()

    def stash_results(pvname: str, response: ReadNotifyResponse):
        try:
            results.append(PVInfoForJ2.from_result(pvname=pvname, response=response))
        except Exception as exc:
            print(exc)

    with Batch() as batch:
        for pv in pvs:
            batch.read(pv, callback=partial(stash_results, pv.name), data_type="control")

    start_time = time.monotonic()
    while time.monotonic() - start_time < 3:
        time.sleep(0.01)
        if len(results) >= len(pvs):
            break

    return results


def main(
    filepath: str,
):
    with open(filepath, "r") as fd:
        deser = json.load(fd)
    all_pvnames = set(pv for pv in walk_dict_pvs(deser))

    if not all_pvnames:
        raise RuntimeError(f"Found zero PVs in {filepath}")

    all_pvinfo = sorted(collect_pv_info(all_pvnames))

    jinja_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(Path(__file__).parent),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = jinja_env.get_template("test_ioc.py.j2")
    rendered = template.render(all_pvinfo=all_pvinfo)
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
