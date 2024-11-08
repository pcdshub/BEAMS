from pathlib import Path

from beams.tree_config import save_tree_item_to_path
from beams.tree_config.action import SetPVActionItem
from beams.tree_config.base import EPICSValue, FixedValue
from beams.tree_config.composite import (SelectorItem, SequenceConditionItem,
                                         SequenceItem)
from beams.tree_config.condition import (BinaryConditionItem,
                                         BoundedConditionItem,
                                         ConditionOperator)
from beams.tree_config.idiom import CheckAndDoItem

# DG2 Stopper: remove
check_dg2_stp_closed = BinaryConditionItem(
    name="check_dg2_stp_closed",
    description="Check that dg2 stopper is at closed switch.",
    left_value=EPICSValue("HFX:DG2:STP:01:CLOSE"),
    operator=ConditionOperator.equal,
    right_value=FixedValue(1),
)
check_dg2_stp_not_open = BinaryConditionItem(
    name="check_dg2_stp_not_open",
    description="Check that dg2 stopper is not at open switch.",
    left_value=EPICSValue("HFX:DG2:STP:01:OPEN"),
    operator=ConditionOperator.equal,
    right_value=FixedValue(0),
)
check_dg2_stp_in = SequenceConditionItem(
    name="check_dg2_stp_in",
    description="Check that dg2 stopper is at the closed switch but not at the open switch.",
    children=[check_dg2_stp_closed, check_dg2_stp_not_open],
)
act_close_dg2_stp = SetPVActionItem(
    name="act_close_dg2_stp",
    description="Move dg2 stopper to block the beam.",
    pv="HFX:DG2:STP:01:CMD",
    value=2,
)
dg2_stopper = CheckAndDoItem(
    name="dg2_stopper",
    description="Ensure that dg2 is inserted before moving focusing optics.",
    check=check_dg2_stp_in,
    do=act_close_dg2_stp,
)

# Prefocusing Lens: remove
pfl_cads = []
for lens in range(3):
    index = lens + 1
    base_pv = f"MFX:LENS:DIA:0{index}"
    state_pv = base_pv + ":STATE"
    remove_pv = base_pv + ":REMOVE"
    pfl_check = BinaryConditionItem(
        name=f"check_pfl{index}_out",
        description="Check if lens is removed",
        left_value=EPICSValue(state_pv),
        operator=ConditionOperator.equal,
        right_value=FixedValue(0),
    )
    pfl_remove = SetPVActionItem(
        name=f"act_pfl{index}_remove",
        description="Remove lens",
        pv=remove_pv,
        value=1,
    )
    pfl_cad = CheckAndDoItem(
        name=f"cad_pfl{index}_remove",
        description="Ensure lens is removed",
        check=pfl_check,
        do=pfl_remove,
    )
    pfl_cads.append(pfl_cad)

prefocus_remove = SequenceItem(
    name="prefocus_remove",
    description="ensure all prefocusing lenses are removed",
    children=pfl_cads,
)

# Transfocator: remove
tfs_cads = []
for lens in range(10):
    index = lens + 1
    base_pv = f"MFX:LENS:TFS:{index:02}"
    state_pv = base_pv + ":STATE"
    remove_pv = base_pv + ":REMOVE"
    tfs_check = BinaryConditionItem(
        name=f"check_tfs{index}_out",
        description="Check if lens is removed",
        left_value=EPICSValue(state_pv),
        operator=ConditionOperator.equal,
        right_value=FixedValue(0),
    )
    tfs_remove = SetPVActionItem(
        name=f"act_tfs{index}_remove",
        description="Remove lens",
        pv=remove_pv,
        value=1,
    )
    tfs_cad = CheckAndDoItem(
        name=f"cad_tfs{index}_remove",
        description="Ensure lens is removed",
        check=tfs_check,
        do=tfs_remove,
    )
    tfs_cads.append(tfs_cad)

transfocator_remove = SequenceItem(
    name="transfocator_remove",
    description="ensure all transfocator lenses are removed",
    children=tfs_cads,
)

# Yags: insert
check_dg1_yag_in = BinaryConditionItem(
    name="check_dg1_yag_in",
    description="Check if the dg1 yag is in",
    left_value=EPICSValue("MFX:DG1:PIM", as_string=True),
    operator=ConditionOperator.equal,
    right_value=FixedValue("YAG"),
)
act_insert_dg1_yag = SetPVActionItem(
    name="act_insert_dg1_yag",
    description="Insert dg1 yag",
    pv="MFX:DG1:PIM:GO",
    value="YAG",
)
dg1_yag = CheckAndDoItem(
    name="dg1_yag",
    description="Ensure dg1_yag is inserted",
    check=check_dg1_yag_in,
    do=act_insert_dg1_yag,
)
check_dg2_yag_in = BinaryConditionItem(
    name="check_dg2_yag_in",
    description="Check if the dg2 yag is in",
    left_value=EPICSValue("MFX:DG2:PIM", as_string=True),
    operator=ConditionOperator.equal,
    right_value=FixedValue("YAG"),
)
act_insert_dg2_yag = SetPVActionItem(
    name="act_insert_dg2_yag",
    description="Insert dg2 yag",
    pv="MFX:DG2:PIM:GO",
    value="YAG",
)
dg2_yag = CheckAndDoItem(
    name="d2_yag",
    description="Ensure dg2_yag is inserted",
    check=check_dg2_yag_in,
    do=act_insert_dg2_yag,
)

# Attenuator: drop to 10%
check_mfx_att_range = BoundedConditionItem(
    name="check_mfx_att_range",
    description="Check if mfx_att is near 10% transmission",
    lower_bound=FixedValue(0.08),
    value=EPICSValue("MFX:ATT:COM:R_CUR"),
    upper_bound=FixedValue(0.12),
)
check_calc_ready = BinaryConditionItem(
    name="check_calc_ready",
    description="Wait for previous or current calc to be done",
    left_value=EPICSValue("MFX:ATT:COM:CALCP"),
    operator=ConditionOperator.equal,
    right_value=FixedValue(0),
)
act_prepare_transmission = SetPVActionItem(
    name="act_prepare_transmission",
    description="Set the transmission that will be applied",
    pv="MFX:ATT:COM:R_DES",
    value=0.1,
)
act_apply_transmission = SetPVActionItem(
    name="act_apply_transmission",
    description="Move the attenuator to the lesser of the two att options",
    pv="MFX:ATT:COM:GO",
    value=3,
    termination_check=check_mfx_att_range,
)
seq_set_mfx_att = SequenceItem(
    name="seq_set_mfx_att",
    description="Set the mfx att to 10% transmission",
    children=[check_calc_ready, act_prepare_transmission, act_apply_transmission],
)
mfx_att = SelectorItem(
    name="mfx_att",
    description="Ensure mfx att is near 10% transmission for alignment",
    children=[check_mfx_att_range, seq_set_mfx_att],
)

# Slits: all to 2mm
slit_cads = []
for slit_name, pv_ext in (
    ("dg1", "DG1:JAWS"),
    ("dg2_us", "DG2:JAWS:US"),
    ("dg2_ms", "DG2:JAWS:MS"),
    ("dg2_ds", "DG2:JAWS:DS"),
):
    base_pv = f"MFX:{pv_ext}:"
    for axis in ("X", "Y"):
        axis_name = f"{slit_name}_{axis.lower()}"
        slit_check = BoundedConditionItem(
            name=f"{axis_name}_check",
            description="Check if slit width is close to 2mm",
            lower_bound=FixedValue(1.9),
            value=EPICSValue(f"{base_pv}Actual_{axis}WIDTH"),
            upper_bound=FixedValue(2.1),
        )
        slit_move = SetPVActionItem(
            name=f"{axis_name}_move",
            description="Move slit width to 2mm",
            pv=f"{base_pv}{axis}WID_REQ",
            value=2,
        )
        slcad = CheckAndDoItem(
            name=f"{axis_name}_check_and_do",
            description="Ensure slit width is close to 2mm",
            check=slit_check,
            do=slit_move,
        )
        slit_cads.append(slcad)
slits_to_2mm = SequenceItem(
    name="slits_to_2mm",
    description="Ensure all slit widths are close to 2mm",
    children=slit_cads,
)

# MR1L4 MFX/MEC mirror
check_mr1l4_xstate = BinaryConditionItem(
    name="check_mr1l4_xstate",
    description="Check if mr1l4 is inserted",
    left_value=EPICSValue("MR1L4:HOMS:MMS:XUP:STATE:GET_RBV"),
    operator=ConditionOperator.equal,
    right_value=FixedValue("IN"),
)
act_mr1l4_xstate = SetPVActionItem(
    name="act_mr1l4_xstate",
    description="Move mr1l4 in",
    pv="MR1L4:HOMS:MMS:XUP:STATE:SET",
    value="IN",
)
insert_mr1l4 = CheckAndDoItem(
    name="insert_mr1l4",
    description="Ensure mr1l4 is in",
    check=check_mr1l4_xstate,
    do=act_mr1l4_xstate,
)
mr1l4_nominal = -544
check_mr1l4_pointing = BoundedConditionItem(
    name="check_mr1l4_pointing",
    description="Check if mr1l4 is pointing generally towards MFX",
    lower_bound=FixedValue(mr1l4_nominal-5),
    value=EPICSValue("MR1L4:HOMS:MMS:PITCH.RBV"),
    upper_bound=FixedValue(mr1l4_nominal+5),
)
act_mr1l4_pitch = SetPVActionItem(
    name="act_mr1l4_pitch",
    description="Move mr1l4 back to the nominal pitch",
    pv="MR1L4:HOMS:MMS:PITCH.VAL",
    value=mr1l4_nominal,
)
point_mr1l4 = CheckAndDoItem(
    name="point_mr1l4",
    description="Ensure mr1l4 is pointed towards MFX",
    check=check_mr1l4_pointing,
    do=act_mr1l4_pitch,
)
prepare_mr1l4 = SequenceItem(
    name="prepare_mr1l4",
    description="Get mr1l4 ready for MFX beam",
    children=[insert_mr1l4, point_mr1l4],
)

# Set up the DG1 camera
check_dg1_cam_running = BinaryConditionItem(
    name="Check_dg1_cam_running",
    description="Check if the camera is acquiring frames",
    left_value=EPICSValue("MFX:DG1:P6740:ArrayRate_RBV"),
    operator=ConditionOperator.greater_equal,
    right_value=FixedValue(1),

)
# If the cam isn't running, it either needs to be turned on, or off and back on
# Simplest is to put the "off" and then the "on" in series without checking.
act_dg1_no_acq = SetPVActionItem(
    name="act_dg1_no_acq",
    description="Stop acquiring",
    pv="MFX:DG1:P6740:Acquire",
    value=0,
)
act_dg1_yes_acq = SetPVActionItem(
    name="act_dg1_yes_acq",
    description="Start acquiring",
    pv="MFX:DG1:P6740:Acquire",
    value=1,
    termination_check=check_dg1_cam_running,
)
seq_dg1_acq_cycle = SequenceItem(
    name="seq_dg1_acq_cycle",
    description="Stop and then start the acquisition",
    children=[act_dg1_no_acq, act_dg1_yes_acq],
)
ensure_dg1_cam_running = SelectorItem(
    name="ensure_dg1_cam_running",
    description="Refresh acquisition if needed",
    children=[check_dg1_cam_running, seq_dg1_acq_cycle],
)
# Skip stats for now


# Full subtree top-level sequence
dg1_prep = SequenceItem(
    name="dg1_prep",
    description="Prepare MFX for alignment to DG1",
    children=[
        dg2_stopper,
        prefocus_remove,
        transfocator_remove,
        dg1_yag,
        dg2_yag,
        mfx_att,
        slits_to_2mm,
        prepare_mr1l4,
        ensure_dg1_cam_running,
    ],
)


def update_mfx_json():
    path = Path(__file__).parent / "mfx_tree.json"
    save_tree_item_to_path(path=path, root=dg1_prep)
