#!/usr/bin/env python3
from textwrap import dedent

from caproto.server import PVGroup, ioc_arg_parser, pvproperty, run


class MockSysResetIOC(PVGroup):
  """
  IOC to mock SLACEPICS IOCs with respect to how they increment heartbeat and are reset
  """

  heartbeat = pvproperty(
        name="HEARTBEAT",
        value=0,
        dtype=int,
        doc="Represents heartbeat of IOC, monotonically increasing (until reset)")
  sys_reset = pvproperty(
        name="SysReset",
        value=0,
        dtype=int,
        doc="Rising edge indicates requested reset, put high to request reset")

  @sys_reset.putter
  async def sys_reset(self, instance, value):
      await self.heartbeat.write(0)
      return 0

  @heartbeat.scan(period=1.0)
  async def heartbeat(self, instance, async_lib):
    print(instance.value)
    await instance.write(instance.value+1)


if __name__ == "__main__":
    ioc_options, run_options = ioc_arg_parser(
        default_prefix="SysResetTest:", desc=dedent(MockSysResetIOC.__doc__)
    )
    ioc = MockSysResetIOC(**ioc_options)
    run(ioc.pvdb, **run_options)
