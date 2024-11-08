import os
from textwrap import dedent

from caproto.server import PVGroup, ioc_arg_parser, pvproperty, run


class BTSimIOC(PVGroup):
    """
    An IOC to replicate the PVs used by your behavior tree.
    """
    hfx_dg2_stp_01_close = pvproperty(
        value=0,
        name="HFX:DG2:STP:01:CLOSE",
        doc="Fake HFX:DG2:STP:01:CLOSE",
    )
    hfx_dg2_stp_01_cmd = pvproperty(
        value=0,
        name="HFX:DG2:STP:01:CMD",
        doc="Fake HFX:DG2:STP:01:CMD",
    )
    hfx_dg2_stp_01_open = pvproperty(
        value=1,
        name="HFX:DG2:STP:01:OPEN",
        doc="Fake HFX:DG2:STP:01:OPEN",
    )
    mfx_att_com_calcp = pvproperty(
        value=0,
        name="MFX:ATT:COM:CALCP",
        doc="Fake MFX:ATT:COM:CALCP",
    )
    mfx_att_com_go = pvproperty(
        value=0,
        name="MFX:ATT:COM:GO",
        doc="Fake MFX:ATT:COM:GO",
    )
    mfx_att_com_r_cur = pvproperty(
        value=1.0,
        name="MFX:ATT:COM:R_CUR",
        doc="Fake MFX:ATT:COM:R_CUR",
    )
    mfx_att_com_r_des = pvproperty(
        value=1.0,
        name="MFX:ATT:COM:R_DES",
        doc="Fake MFX:ATT:COM:R_DES",
    )
    mfx_dg1_jaws_actual_xwidth = pvproperty(
        value=5.0,
        name="MFX:DG1:JAWS:Actual_XWIDTH",
        doc="Fake MFX:DG1:JAWS:Actual_XWIDTH",
    )
    mfx_dg1_jaws_actual_ywidth = pvproperty(
        value=5.0,
        name="MFX:DG1:JAWS:Actual_YWIDTH",
        doc="Fake MFX:DG1:JAWS:Actual_YWIDTH",
    )
    mfx_dg1_jaws_xwid_req = pvproperty(
        value=5.0,
        name="MFX:DG1:JAWS:XWID_REQ",
        doc="Fake MFX:DG1:JAWS:XWID_REQ",
    )
    mfx_dg1_jaws_ywid_req = pvproperty(
        value=5.0,
        name="MFX:DG1:JAWS:YWID_REQ",
        doc="Fake MFX:DG1:JAWS:YWID_REQ",
    )
    mfx_dg1_p6740_acquire = pvproperty(
        value=1,
        name="MFX:DG1:P6740:Acquire",
        doc="Fake MFX:DG1:P6740:Acquire",
    )
    mfx_dg1_p6740_arrayrate_rbv = pvproperty(
        value=0.0,
        name="MFX:DG1:P6740:ArrayRate_RBV",
        doc="Fake MFX:DG1:P6740:ArrayRate_RBV",
    )
    mfx_dg1_pim = pvproperty(
        value="OUT",
        name="MFX:DG1:PIM",
        doc="Fake MFX:DG1:PIM",
    )
    mfx_dg1_pim_go = pvproperty(
        value="OUT",
        name="MFX:DG1:PIM:GO",
        doc="Fake MFX:DG1:PIM:GO",
    )
    mfx_dg2_jaws_ds_actual_xwidth = pvproperty(
        value=1.0,
        name="MFX:DG2:JAWS:DS:Actual_XWIDTH",
        doc="Fake MFX:DG2:JAWS:DS:Actual_XWIDTH",
    )
    mfx_dg2_jaws_ds_actual_ywidth = pvproperty(
        value=1.0,
        name="MFX:DG2:JAWS:DS:Actual_YWIDTH",
        doc="Fake MFX:DG2:JAWS:DS:Actual_YWIDTH",
    )
    mfx_dg2_jaws_ds_xwid_req = pvproperty(
        value=1.0,
        name="MFX:DG2:JAWS:DS:XWID_REQ",
        doc="Fake MFX:DG2:JAWS:DS:XWID_REQ",
    )
    mfx_dg2_jaws_ds_ywid_req = pvproperty(
        value=1.0,
        name="MFX:DG2:JAWS:DS:YWID_REQ",
        doc="Fake MFX:DG2:JAWS:DS:YWID_REQ",
    )
    mfx_dg2_jaws_ms_actual_xwidth = pvproperty(
        value=0.5,
        name="MFX:DG2:JAWS:MS:Actual_XWIDTH",
        doc="Fake MFX:DG2:JAWS:MS:Actual_XWIDTH",
    )
    mfx_dg2_jaws_ms_actual_ywidth = pvproperty(
        value=0.5,
        name="MFX:DG2:JAWS:MS:Actual_YWIDTH",
        doc="Fake MFX:DG2:JAWS:MS:Actual_YWIDTH",
    )
    mfx_dg2_jaws_ms_xwid_req = pvproperty(
        value=0.5,
        name="MFX:DG2:JAWS:MS:XWID_REQ",
        doc="Fake MFX:DG2:JAWS:MS:XWID_REQ",
    )
    mfx_dg2_jaws_ms_ywid_req = pvproperty(
        value=0.5,
        name="MFX:DG2:JAWS:MS:YWID_REQ",
        doc="Fake MFX:DG2:JAWS:MS:YWID_REQ",
    )
    mfx_dg2_jaws_us_actual_xwidth = pvproperty(
        value=0.5,
        name="MFX:DG2:JAWS:US:Actual_XWIDTH",
        doc="Fake MFX:DG2:JAWS:US:Actual_XWIDTH",
    )
    mfx_dg2_jaws_us_actual_ywidth = pvproperty(
        value=0.5,
        name="MFX:DG2:JAWS:US:Actual_YWIDTH",
        doc="Fake MFX:DG2:JAWS:US:Actual_YWIDTH",
    )
    mfx_dg2_jaws_us_xwid_req = pvproperty(
        value=0.5,
        name="MFX:DG2:JAWS:US:XWID_REQ",
        doc="Fake MFX:DG2:JAWS:US:XWID_REQ",
    )
    mfx_dg2_jaws_us_ywid_req = pvproperty(
        value=0.5,
        name="MFX:DG2:JAWS:US:YWID_REQ",
        doc="Fake MFX:DG2:JAWS:US:YWID_REQ",
    )
    mfx_dg2_pim = pvproperty(
        value="OUT",
        name="MFX:DG2:PIM",
        doc="Fake MFX:DG2:PIM",
    )
    mfx_dg2_pim_go = pvproperty(
        value="OUT",
        name="MFX:DG2:PIM:GO",
        doc="Fake MFX:DG2:PIM:GO",
    )
    mfx_lens_dia_01_remove = pvproperty(
        value=0,
        name="MFX:LENS:DIA:01:REMOVE",
        doc="Fake MFX:LENS:DIA:01:REMOVE",
    )
    mfx_lens_dia_01_state = pvproperty(
        value=1,
        name="MFX:LENS:DIA:01:STATE",
        doc="Fake MFX:LENS:DIA:01:STATE",
    )
    mfx_lens_dia_02_remove = pvproperty(
        value=0,
        name="MFX:LENS:DIA:02:REMOVE",
        doc="Fake MFX:LENS:DIA:02:REMOVE",
    )
    mfx_lens_dia_02_state = pvproperty(
        value=0,
        name="MFX:LENS:DIA:02:STATE",
        doc="Fake MFX:LENS:DIA:02:STATE",
    )
    mfx_lens_dia_03_remove = pvproperty(
        value=0,
        name="MFX:LENS:DIA:03:REMOVE",
        doc="Fake MFX:LENS:DIA:03:REMOVE",
    )
    mfx_lens_dia_03_state = pvproperty(
        value=0,
        name="MFX:LENS:DIA:03:STATE",
        doc="Fake MFX:LENS:DIA:03:STATE",
    )
    mfx_lens_tfs_01_remove = pvproperty(
        value=0,
        name="MFX:LENS:TFS:01:REMOVE",
        doc="Fake MFX:LENS:TFS:01:REMOVE",
    )
    mfx_lens_tfs_01_state = pvproperty(
        value=1,
        name="MFX:LENS:TFS:01:STATE",
        doc="Fake MFX:LENS:TFS:01:STATE",
    )
    mfx_lens_tfs_02_remove = pvproperty(
        value=0,
        name="MFX:LENS:TFS:02:REMOVE",
        doc="Fake MFX:LENS:TFS:02:REMOVE",
    )
    mfx_lens_tfs_02_state = pvproperty(
        value=0,
        name="MFX:LENS:TFS:02:STATE",
        doc="Fake MFX:LENS:TFS:02:STATE",
    )
    mfx_lens_tfs_03_remove = pvproperty(
        value=0,
        name="MFX:LENS:TFS:03:REMOVE",
        doc="Fake MFX:LENS:TFS:03:REMOVE",
    )
    mfx_lens_tfs_03_state = pvproperty(
        value=1,
        name="MFX:LENS:TFS:03:STATE",
        doc="Fake MFX:LENS:TFS:03:STATE",
    )
    mfx_lens_tfs_04_remove = pvproperty(
        value=0,
        name="MFX:LENS:TFS:04:REMOVE",
        doc="Fake MFX:LENS:TFS:04:REMOVE",
    )
    mfx_lens_tfs_04_state = pvproperty(
        value=0,
        name="MFX:LENS:TFS:04:STATE",
        doc="Fake MFX:LENS:TFS:04:STATE",
    )
    mfx_lens_tfs_05_remove = pvproperty(
        value=0,
        name="MFX:LENS:TFS:05:REMOVE",
        doc="Fake MFX:LENS:TFS:05:REMOVE",
    )
    mfx_lens_tfs_05_state = pvproperty(
        value=1,
        name="MFX:LENS:TFS:05:STATE",
        doc="Fake MFX:LENS:TFS:05:STATE",
    )
    mfx_lens_tfs_06_remove = pvproperty(
        value=0,
        name="MFX:LENS:TFS:06:REMOVE",
        doc="Fake MFX:LENS:TFS:06:REMOVE",
    )
    mfx_lens_tfs_06_state = pvproperty(
        value=0,
        name="MFX:LENS:TFS:06:STATE",
        doc="Fake MFX:LENS:TFS:06:STATE",
    )
    mfx_lens_tfs_07_remove = pvproperty(
        value=1,
        name="MFX:LENS:TFS:07:REMOVE",
        doc="Fake MFX:LENS:TFS:07:REMOVE",
    )
    mfx_lens_tfs_07_state = pvproperty(
        value=0,
        name="MFX:LENS:TFS:07:STATE",
        doc="Fake MFX:LENS:TFS:07:STATE",
    )
    mfx_lens_tfs_08_remove = pvproperty(
        value=0,
        name="MFX:LENS:TFS:08:REMOVE",
        doc="Fake MFX:LENS:TFS:08:REMOVE",
    )
    mfx_lens_tfs_08_state = pvproperty(
        value=0,
        name="MFX:LENS:TFS:08:STATE",
        doc="Fake MFX:LENS:TFS:08:STATE",
    )
    mfx_lens_tfs_09_remove = pvproperty(
        value=1,
        name="MFX:LENS:TFS:09:REMOVE",
        doc="Fake MFX:LENS:TFS:09:REMOVE",
    )
    mfx_lens_tfs_09_state = pvproperty(
        value=0,
        name="MFX:LENS:TFS:09:STATE",
        doc="Fake MFX:LENS:TFS:09:STATE",
    )
    mfx_lens_tfs_10_remove = pvproperty(
        value=0,
        name="MFX:LENS:TFS:10:REMOVE",
        doc="Fake MFX:LENS:TFS:10:REMOVE",
    )
    mfx_lens_tfs_10_state = pvproperty(
        value=1,
        name="MFX:LENS:TFS:10:STATE",
        doc="Fake MFX:LENS:TFS:10:STATE",
    )
    mr1l4_homs_mms_pitch_rbv = pvproperty(
        value=833.4,
        name="MR1L4:HOMS:MMS:PITCH.RBV",
        doc="Fake MR1L4:HOMS:MMS:PITCH.RBV",
    )
    mr1l4_homs_mms_pitch_val = pvproperty(
        value=833.4,
        name="MR1L4:HOMS:MMS:PITCH.VAL",
        doc="Fake MR1L4:HOMS:MMS:PITCH.VAL",
    )
    mr1l4_homs_mms_xup_state_get_rbv = pvproperty(
        value="OUT",
        name="MR1L4:HOMS:MMS:XUP:STATE:GET_RBV",
        doc="Fake MR1L4:HOMS:MMS:XUP:STATE:GET_RBV",
    )
    mr1l4_homs_mms_xup_state_set = pvproperty(
        value="OUT",
        name="MR1L4:HOMS:MMS:XUP:STATE:SET",
        doc="Fake MR1L4:HOMS:MMS:XUP:STATE:SET",
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
