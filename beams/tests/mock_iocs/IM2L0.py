#!/usr/bin/env python3
from enum import StrEnum, auto
from textwrap import dedent
from caproto.server import PVGroup, ioc_arg_parser, pvproperty, run


class TargetState(StrEnum):
    UNKOWN = auto()
    OUT = auto()
    YAG = auto()
    DIAMOND = auto()
    RETICLE = auto()


class FilterWheelValue(StrEnum):
    UNKOWN = auto()
    T1 = auto()
    T5 = auto()
    T10 = auto()
    T25 = auto()
    T50 = auto()
    T100 = auto()


class MockIML20(PVGroup):
    """
    An IOC with three uncoupled read/writable PVs.

    Scalar PVs
    ----------
    """

    im2l0_target = pvproperty(
        name="MMS:STATE:GET_RBV",
        value=f"{TargetState.UNKOWN.value.upper()}",
        dtype=str,
        doc=f"Represents state of simulated imager target. Options {[i.upper() for i in TargetState]}",
        max_length=10,
    )
    im2l0_zoom_motor = pvproperty(
        name="CLZ.RBV",
        value=0,
        dtype=float,
        doc="Represents percentage of zoom actuated by zoom motor",
    )
    im2l0_focus_motor = pvproperty(
        name="CLF.RBV",
        value=0,
        dtype=float,
        doc="Represents percentage of zoom actuated by zoom motor",
    )
    im2l0_filter_wheel = pvproperty(
        name="MFW:GET_RBV",
        value=f"{FilterWheelValue.UNKOWN.value.upper()}",
        dtype=str,
        doc=f"Represents filter wheel value. Options {[i.upper() for i in FilterWheelValue]}",
        max_length=10,
    )


if __name__ == "__main__":
    ioc_options, run_options = ioc_arg_parser(
        default_prefix="IM2L0:XTES:", desc=dedent(MockIML20.__doc__)
    )
    ioc = MockIML20(**ioc_options)
    run(ioc.pvdb, **run_options)
