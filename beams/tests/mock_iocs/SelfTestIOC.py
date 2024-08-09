#!/usr/bin/env python3
from textwrap import dedent

from caproto.server import PVGroup, ioc_arg_parser, pvproperty, run


class SelfTestIOC(PVGroup):
    """
    An IOC with three uncoupled read/writable PVs.

    Scalar PVs
    ----------
    COMP (int)
    """

    COMP = pvproperty(
        value=1,
        doc="Represents percentage complete (out of 100) for the SELF_TEST tree",
    )


if __name__ == "__main__":
    ioc_options, run_options = ioc_arg_parser(
        default_prefix="PERC:", desc=dedent(SelfTestIOC.__doc__)
    )
    ioc = SelfTestIOC(**ioc_options)
    run(ioc.pvdb, **run_options)
