#!/usr/bin/env python3
from enum import Enum
from random import random
from textwrap import dedent

from caproto.server import PVGroup, ioc_arg_parser, pvproperty, run


class TargetState(str, Enum):
    UNKNOWN = "UNKNOWN"
    OUT = "OUT"
    YAG = "YAG"
    DIAMOND = "DIAMOND"
    RETICLE = "RETICLE"


class FilterWheelValue(str, Enum):
    UNKNOWN = "UNKNOWN"
    T1 = "T1"
    T5 = "T5"
    T10 = "T10"
    T25 = "T25"
    T50 = "T50"
    T100 = "T100"


class MockIML20(PVGroup):
    """
    # An IOC with three uncoupled read/writable PVs.

    # Scalar PVs:
        * IM2L0:XTES:CLZ.RBV - Zoom motor percentage of actuation
        * IM2L0:XTES:CLF.RBV - Focus motor percentage of actuation
    * Enum PVs:
        * IM2L0:XTES:MMS:STATE:GET_RBV - enumerated state of imager target
        * IM2L0:XTES:MFW:GET_RBV - enumerated state of filter wheel "actuation"
    ----------
    """

    im2l0_target = pvproperty(
        name="MMS:STATE:GET_RBV",
        value=f"{TargetState.UNKNOWN.value.upper()}",
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
        doc="Represents percentage of focus actuated by focus motor",
    )
    im2l0_filter_wheel = pvproperty(
        name="MFW:GET_RBV",
        value=f"{FilterWheelValue.UNKNOWN.value.upper()}",
        dtype=str,
        doc=f"Represents filter wheel value. Options {[i.upper() for i in FilterWheelValue]}",
        max_length=10,
    )

    @im2l0_zoom_motor.putter
    async def im2l0_zoom_motor(self, instance, value):
        noise = (0.5 - random()) * 0.2
        return value + noise


if __name__ == "__main__":
    ioc_options, run_options = ioc_arg_parser(
        default_prefix="IM2L0:XTES:", desc=dedent(MockIML20.__doc__)
    )
    ioc = MockIML20(**ioc_options)
    run(ioc.pvdb, **run_options)
