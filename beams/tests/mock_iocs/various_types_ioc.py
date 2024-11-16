#!/usr/bin/env python3
from textwrap import dedent

from caproto import ChannelType
from caproto.server import PVGroup, ioc_arg_parser, pvproperty, run


class VariousTypesIOC(PVGroup):
    """
    An IOC with PVs of various types.

    Used to test the IOC inspection/generation tooling.
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
        value=0,
        dtype=ChannelType.ENUM,
        enum_strings=["apple", "pumpkin", "shepherd's"]
    )


if __name__ == "__main__":
    ioc_options, run_options = ioc_arg_parser(
        default_prefix="VAR:TYPES:", desc=dedent(VariousTypesIOC.__doc__)
    )
    ioc = VariousTypesIOC(**ioc_options)
    run(ioc.pvdb, **run_options)
