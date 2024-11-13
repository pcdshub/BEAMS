import os
from textwrap import dedent

from caproto import ChannelType
from caproto.server import PVGroup, ioc_arg_parser, pvproperty, run


class BTSimIOC(PVGroup):
    """
    An IOC to replicate the PVs used by your behavior tree.
    """
    hfx_dg2_stp_01_close = pvproperty(
        name="HFX:DG2:STP:01:CLOSE",
        doc="Fake HFX:DG2:STP:01:CLOSE",
        value=1,
        dtype=ChannelType.ENUM,
        enum_strings=['Inactive', 'Active'],
    )
    hfx_dg2_stp_01_cmd = pvproperty(
        name="HFX:DG2:STP:01:CMD",
        doc="Fake HFX:DG2:STP:01:CMD",
        value=0,
        dtype=ChannelType.ENUM,
        enum_strings=['CLOSE', 'OPEN'],
    )
    hfx_dg2_stp_01_open = pvproperty(
        name="HFX:DG2:STP:01:OPEN",
        doc="Fake HFX:DG2:STP:01:OPEN",
        value=0,
        dtype=ChannelType.ENUM,
        enum_strings=['Inactive', 'Active'],
    )
    mfx_att_com_calcp = pvproperty(
        name="MFX:ATT:COM:CALCP",
        doc="Fake MFX:ATT:COM:CALCP",
        value=0,
        dtype=ChannelType.ENUM,
        enum_strings=['No', 'Yes'],
    )
    mfx_att_com_go = pvproperty(
        name="MFX:ATT:COM:GO",
        doc="Fake MFX:ATT:COM:GO",
        value=1,
        dtype=ChannelType.ENUM,
        enum_strings=['All OUT', 'All IN', 'Ceiling', 'Floor'],
    )
    mfx_att_com_r_cur = pvproperty(
        name="MFX:ATT:COM:R_CUR",
        doc="Fake MFX:ATT:COM:R_CUR",
        value=5.899902216596077e-178,
        dtype=ChannelType.DOUBLE,
    )
    mfx_att_com_r_des = pvproperty(
        name="MFX:ATT:COM:R_DES",
        doc="Fake MFX:ATT:COM:R_DES",
        value=1e-05,
        dtype=ChannelType.DOUBLE,
    )
    mfx_dg1_jaws_actual_xwidth = pvproperty(
        name="MFX:DG1:JAWS:ACTUAL_XWIDTH",
        doc="Fake MFX:DG1:JAWS:ACTUAL_XWIDTH",
        value=0.9995,
        dtype=ChannelType.DOUBLE,
    )
    mfx_dg1_jaws_actual_ywidth = pvproperty(
        name="MFX:DG1:JAWS:ACTUAL_YWIDTH",
        doc="Fake MFX:DG1:JAWS:ACTUAL_YWIDTH",
        value=0.9995999999999998,
        dtype=ChannelType.DOUBLE,
    )
    mfx_dg1_jaws_xwid_req = pvproperty(
        name="MFX:DG1:JAWS:XWID_REQ",
        doc="Fake MFX:DG1:JAWS:XWID_REQ",
        value=1.0,
        dtype=ChannelType.DOUBLE,
    )
    mfx_dg1_jaws_ywid_req = pvproperty(
        name="MFX:DG1:JAWS:YWID_REQ",
        doc="Fake MFX:DG1:JAWS:YWID_REQ",
        value=1.0,
        dtype=ChannelType.DOUBLE,
    )
    mfx_dg1_p6740_acquire = pvproperty(
        name="MFX:DG1:P6740:Acquire",
        doc="Fake MFX:DG1:P6740:Acquire",
        value=1,
        dtype=ChannelType.ENUM,
        enum_strings=['Done', 'Acquire'],
    )
    mfx_dg1_p6740_acquire_rbv = pvproperty(
        name="MFX:DG1:P6740:Acquire_RBV",
        doc="Fake MFX:DG1:P6740:Acquire_RBV",
        value=1,
        dtype=ChannelType.ENUM,
        enum_strings=['Done', 'Acquiring'],
    )
    mfx_dg1_p6740_arrayrate_rbv = pvproperty(
        name="MFX:DG1:P6740:ArrayRate_RBV",
        doc="Fake MFX:DG1:P6740:ArrayRate_RBV",
        value=10.0,
        dtype=ChannelType.DOUBLE,
    )
    mfx_dg1_pim = pvproperty(
        name="MFX:DG1:PIM",
        doc="Fake MFX:DG1:PIM",
        value=2,
        dtype=ChannelType.ENUM,
        enum_strings=['Unknown', 'YAG', 'OUT'],
    )
    mfx_dg1_pim_go = pvproperty(
        name="MFX:DG1:PIM:GO",
        doc="Fake MFX:DG1:PIM:GO",
        value=0,
        dtype=ChannelType.ENUM,
        enum_strings=['Unknown', 'YAG', 'OUT'],
    )
    mfx_dg2_jaws_ds_actual_xwidth = pvproperty(
        name="MFX:DG2:JAWS:DS:ACTUAL_XWIDTH",
        doc="Fake MFX:DG2:JAWS:DS:ACTUAL_XWIDTH",
        value=4.9996,
        dtype=ChannelType.DOUBLE,
    )
    mfx_dg2_jaws_ds_actual_ywidth = pvproperty(
        name="MFX:DG2:JAWS:DS:ACTUAL_YWIDTH",
        doc="Fake MFX:DG2:JAWS:DS:ACTUAL_YWIDTH",
        value=4.999815806,
        dtype=ChannelType.DOUBLE,
    )
    mfx_dg2_jaws_ds_xwid_req = pvproperty(
        name="MFX:DG2:JAWS:DS:XWID_REQ",
        doc="Fake MFX:DG2:JAWS:DS:XWID_REQ",
        value=5.0,
        dtype=ChannelType.DOUBLE,
    )
    mfx_dg2_jaws_ds_ywid_req = pvproperty(
        name="MFX:DG2:JAWS:DS:YWID_REQ",
        doc="Fake MFX:DG2:JAWS:DS:YWID_REQ",
        value=5.0,
        dtype=ChannelType.DOUBLE,
    )
    mfx_dg2_jaws_ms_actual_xwidth = pvproperty(
        name="MFX:DG2:JAWS:MS:ACTUAL_XWIDTH",
        doc="Fake MFX:DG2:JAWS:MS:ACTUAL_XWIDTH",
        value=5.0006,
        dtype=ChannelType.DOUBLE,
    )
    mfx_dg2_jaws_ms_actual_ywidth = pvproperty(
        name="MFX:DG2:JAWS:MS:ACTUAL_YWIDTH",
        doc="Fake MFX:DG2:JAWS:MS:ACTUAL_YWIDTH",
        value=4.9993,
        dtype=ChannelType.DOUBLE,
    )
    mfx_dg2_jaws_ms_xwid_req = pvproperty(
        name="MFX:DG2:JAWS:MS:XWID_REQ",
        doc="Fake MFX:DG2:JAWS:MS:XWID_REQ",
        value=5.0,
        dtype=ChannelType.DOUBLE,
    )
    mfx_dg2_jaws_ms_ywid_req = pvproperty(
        name="MFX:DG2:JAWS:MS:YWID_REQ",
        doc="Fake MFX:DG2:JAWS:MS:YWID_REQ",
        value=5.0,
        dtype=ChannelType.DOUBLE,
    )
    mfx_dg2_jaws_us_actual_xwidth = pvproperty(
        name="MFX:DG2:JAWS:US:ACTUAL_XWIDTH",
        doc="Fake MFX:DG2:JAWS:US:ACTUAL_XWIDTH",
        value=0.9990999999999985,
        dtype=ChannelType.DOUBLE,
    )
    mfx_dg2_jaws_us_actual_ywidth = pvproperty(
        name="MFX:DG2:JAWS:US:ACTUAL_YWIDTH",
        doc="Fake MFX:DG2:JAWS:US:ACTUAL_YWIDTH",
        value=0.9998,
        dtype=ChannelType.DOUBLE,
    )
    mfx_dg2_jaws_us_xwid_req = pvproperty(
        name="MFX:DG2:JAWS:US:XWID_REQ",
        doc="Fake MFX:DG2:JAWS:US:XWID_REQ",
        value=1.0,
        dtype=ChannelType.DOUBLE,
    )
    mfx_dg2_jaws_us_ywid_req = pvproperty(
        name="MFX:DG2:JAWS:US:YWID_REQ",
        doc="Fake MFX:DG2:JAWS:US:YWID_REQ",
        value=1.0,
        dtype=ChannelType.DOUBLE,
    )
    mfx_dg2_pim = pvproperty(
        name="MFX:DG2:PIM",
        doc="Fake MFX:DG2:PIM",
        value=2,
        dtype=ChannelType.ENUM,
        enum_strings=['Unknown', 'YAG', 'OUT'],
    )
    mfx_dg2_pim_go = pvproperty(
        name="MFX:DG2:PIM:GO",
        doc="Fake MFX:DG2:PIM:GO",
        value=0,
        dtype=ChannelType.ENUM,
        enum_strings=['Unknown', 'YAG', 'OUT'],
    )
    mfx_lens_dia_01_remove = pvproperty(
        name="MFX:LENS:DIA:01:REMOVE",
        doc="Fake MFX:LENS:DIA:01:REMOVE",
        value=0,
        dtype=ChannelType.ENUM,
        enum_strings=['NO', 'OUT'],
    )
    mfx_lens_dia_01_state = pvproperty(
        name="MFX:LENS:DIA:01:STATE",
        doc="Fake MFX:LENS:DIA:01:STATE",
        value=0,
        dtype=ChannelType.ENUM,
        enum_strings=['Not in', 'In'],
    )
    mfx_lens_dia_02_remove = pvproperty(
        name="MFX:LENS:DIA:02:REMOVE",
        doc="Fake MFX:LENS:DIA:02:REMOVE",
        value=0,
        dtype=ChannelType.ENUM,
        enum_strings=['NO', 'OUT'],
    )
    mfx_lens_dia_02_state = pvproperty(
        name="MFX:LENS:DIA:02:STATE",
        doc="Fake MFX:LENS:DIA:02:STATE",
        value=0,
        dtype=ChannelType.ENUM,
        enum_strings=['Not in', 'In'],
    )
    mfx_lens_dia_03_remove = pvproperty(
        name="MFX:LENS:DIA:03:REMOVE",
        doc="Fake MFX:LENS:DIA:03:REMOVE",
        value=0,
        dtype=ChannelType.ENUM,
        enum_strings=['NO', 'OUT'],
    )
    mfx_lens_dia_03_state = pvproperty(
        name="MFX:LENS:DIA:03:STATE",
        doc="Fake MFX:LENS:DIA:03:STATE",
        value=0,
        dtype=ChannelType.ENUM,
        enum_strings=['Not in', 'In'],
    )
    mfx_lens_tfs_01_remove = pvproperty(
        name="MFX:LENS:TFS:01:REMOVE",
        doc="Fake MFX:LENS:TFS:01:REMOVE",
        value=0,
        dtype=ChannelType.ENUM,
        enum_strings=['NO', 'OUT'],
    )
    mfx_lens_tfs_01_state = pvproperty(
        name="MFX:LENS:TFS:01:STATE",
        doc="Fake MFX:LENS:TFS:01:STATE",
        value=0,
        dtype=ChannelType.ENUM,
        enum_strings=['Not in', 'In'],
    )
    mfx_lens_tfs_02_remove = pvproperty(
        name="MFX:LENS:TFS:02:REMOVE",
        doc="Fake MFX:LENS:TFS:02:REMOVE",
        value=0,
        dtype=ChannelType.ENUM,
        enum_strings=['NO', 'OUT'],
    )
    mfx_lens_tfs_02_state = pvproperty(
        name="MFX:LENS:TFS:02:STATE",
        doc="Fake MFX:LENS:TFS:02:STATE",
        value=0,
        dtype=ChannelType.ENUM,
        enum_strings=['Not in', 'In'],
    )
    mfx_lens_tfs_03_remove = pvproperty(
        name="MFX:LENS:TFS:03:REMOVE",
        doc="Fake MFX:LENS:TFS:03:REMOVE",
        value=0,
        dtype=ChannelType.ENUM,
        enum_strings=['NO', 'OUT'],
    )
    mfx_lens_tfs_03_state = pvproperty(
        name="MFX:LENS:TFS:03:STATE",
        doc="Fake MFX:LENS:TFS:03:STATE",
        value=0,
        dtype=ChannelType.ENUM,
        enum_strings=['Not in', 'In'],
    )
    mfx_lens_tfs_04_remove = pvproperty(
        name="MFX:LENS:TFS:04:REMOVE",
        doc="Fake MFX:LENS:TFS:04:REMOVE",
        value=0,
        dtype=ChannelType.ENUM,
        enum_strings=['NO', 'OUT'],
    )
    mfx_lens_tfs_04_state = pvproperty(
        name="MFX:LENS:TFS:04:STATE",
        doc="Fake MFX:LENS:TFS:04:STATE",
        value=0,
        dtype=ChannelType.ENUM,
        enum_strings=['Not in', 'In'],
    )
    mfx_lens_tfs_05_remove = pvproperty(
        name="MFX:LENS:TFS:05:REMOVE",
        doc="Fake MFX:LENS:TFS:05:REMOVE",
        value=0,
        dtype=ChannelType.ENUM,
        enum_strings=['NO', 'OUT'],
    )
    mfx_lens_tfs_05_state = pvproperty(
        name="MFX:LENS:TFS:05:STATE",
        doc="Fake MFX:LENS:TFS:05:STATE",
        value=0,
        dtype=ChannelType.ENUM,
        enum_strings=['Not in', 'In'],
    )
    mfx_lens_tfs_06_remove = pvproperty(
        name="MFX:LENS:TFS:06:REMOVE",
        doc="Fake MFX:LENS:TFS:06:REMOVE",
        value=0,
        dtype=ChannelType.ENUM,
        enum_strings=['NO', 'OUT'],
    )
    mfx_lens_tfs_06_state = pvproperty(
        name="MFX:LENS:TFS:06:STATE",
        doc="Fake MFX:LENS:TFS:06:STATE",
        value=0,
        dtype=ChannelType.ENUM,
        enum_strings=['Not in', 'In'],
    )
    mfx_lens_tfs_07_remove = pvproperty(
        name="MFX:LENS:TFS:07:REMOVE",
        doc="Fake MFX:LENS:TFS:07:REMOVE",
        value=0,
        dtype=ChannelType.ENUM,
        enum_strings=['NO', 'OUT'],
    )
    mfx_lens_tfs_07_state = pvproperty(
        name="MFX:LENS:TFS:07:STATE",
        doc="Fake MFX:LENS:TFS:07:STATE",
        value=0,
        dtype=ChannelType.ENUM,
        enum_strings=['Not in', 'In'],
    )
    mfx_lens_tfs_08_remove = pvproperty(
        name="MFX:LENS:TFS:08:REMOVE",
        doc="Fake MFX:LENS:TFS:08:REMOVE",
        value=0,
        dtype=ChannelType.ENUM,
        enum_strings=['NO', 'OUT'],
    )
    mfx_lens_tfs_08_state = pvproperty(
        name="MFX:LENS:TFS:08:STATE",
        doc="Fake MFX:LENS:TFS:08:STATE",
        value=0,
        dtype=ChannelType.ENUM,
        enum_strings=['Not in', 'In'],
    )
    mfx_lens_tfs_09_remove = pvproperty(
        name="MFX:LENS:TFS:09:REMOVE",
        doc="Fake MFX:LENS:TFS:09:REMOVE",
        value=0,
        dtype=ChannelType.ENUM,
        enum_strings=['NO', 'OUT'],
    )
    mfx_lens_tfs_09_state = pvproperty(
        name="MFX:LENS:TFS:09:STATE",
        doc="Fake MFX:LENS:TFS:09:STATE",
        value=0,
        dtype=ChannelType.ENUM,
        enum_strings=['Not in', 'In'],
    )
    mfx_lens_tfs_10_remove = pvproperty(
        name="MFX:LENS:TFS:10:REMOVE",
        doc="Fake MFX:LENS:TFS:10:REMOVE",
        value=0,
        dtype=ChannelType.ENUM,
        enum_strings=['NO', 'OUT'],
    )
    mfx_lens_tfs_10_state = pvproperty(
        name="MFX:LENS:TFS:10:STATE",
        doc="Fake MFX:LENS:TFS:10:STATE",
        value=0,
        dtype=ChannelType.ENUM,
        enum_strings=['Not in', 'In'],
    )
    mr1l4_homs_mms_pitch_rbv = pvproperty(
        name="MR1L4:HOMS:MMS:PITCH.RBV",
        doc="Fake MR1L4:HOMS:MMS:PITCH.RBV",
        value=840.547343,
        dtype=ChannelType.DOUBLE,
    )
    mr1l4_homs_mms_pitch_val = pvproperty(
        name="MR1L4:HOMS:MMS:PITCH.VAL",
        doc="Fake MR1L4:HOMS:MMS:PITCH.VAL",
        value=840.5500000000001,
        dtype=ChannelType.DOUBLE,
    )
    mr1l4_homs_mms_xup_state_get_rbv = pvproperty(
        name="MR1L4:HOMS:MMS:XUP:STATE:GET_RBV",
        doc="Fake MR1L4:HOMS:MMS:XUP:STATE:GET_RBV",
        value=1,
        dtype=ChannelType.ENUM,
        enum_strings=['UNKNOWN', 'OUT', 'IN'],
    )
    mr1l4_homs_mms_xup_state_set = pvproperty(
        name="MR1L4:HOMS:MMS:XUP:STATE:SET",
        doc="Fake MR1L4:HOMS:MMS:XUP:STATE:SET",
        value=1,
        dtype=ChannelType.ENUM,
        enum_strings=['UNKNOWN', 'OUT', 'IN'],
    )


if __name__ == '__main__':
    # Default is 5064, switch to 5066 to avoid conflict with prod
    # Set this in terminal before you run your tree too to connect to this sim
    os.environ["EPICS_CA_SERVER_PORT"] = "5066"
    ioc_options, run_options = ioc_arg_parser(
        default_prefix='',
        desc=dedent(BTSimIOC.__doc__))
    ioc = BTSimIOC(**ioc_options)
    run(ioc.pvdb, **run_options)
