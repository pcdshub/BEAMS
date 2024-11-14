#!/usr/bin/env python3
from textwrap import dedent

from caproto import ChannelType
from caproto.server import PVGroup, ioc_arg_parser, pvproperty, run


class VariousTypesIOC(PVGroup):
    """
    An IOC with three uncoupled read/writable PVs.

    Scalar PVs
    ----------
    COMP (int)
    """

    INT = pvproperty(
        value=3,
        dtype=ChannelType.INT,
    )

    FLOAT = pvproperty(
        value=3.14,
        dtype=ChannelType.FLOAT,
        precision=3,
    )

    STRING = pvproperty(
        value="pi",
        dtype=ChannelType.STRING,
    )

    ENUM = pvproperty(
        value=2,
        dtype=ChannelType.ENUM,
        enum_strings=["e", "i", "pi"]
    )


if __name__ == "__main__":
    ioc_options, run_options = ioc_arg_parser(
        default_prefix="VAR:TYPES:", desc=dedent(VariousTypesIOC.__doc__)
    )
    ioc = VariousTypesIOC(**ioc_options)
    run(ioc.pvdb, **run_options)
