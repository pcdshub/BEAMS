#!/usr/bin/env python3
from textwrap import dedent

from caproto.server import PVGroup, ioc_arg_parser, pvproperty, run


class MockImager(PVGroup):
    """
    An IOC with three uncoupled read/writable PVs.

    Scalar PVs
    ----------
    COMP (int)
    """

    FOUND = pvproperty(
        value=0,
        doc="Represents if simulated reticule is found",
    )
    INSERT = pvproperty(
        value=0,
        doc="Represents if simulated reticule is inserted",
    )


if __name__ == "__main__":
    ioc_options, run_options = ioc_arg_parser(
        default_prefix="RET:", desc=dedent(MockImager.__doc__)
    )
    ioc = MockImager(**ioc_options)
    run(ioc.pvdb, **run_options)
