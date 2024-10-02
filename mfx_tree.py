from beams.tree_config import CheckAndDoItem, ConditionItem, SetPVActionItem, ConditionOperator, SequenceItem, SequenceConditionItem, RangeConditionItem

# DG2 Stopper: remove
check_dg2_stp_closed = ConditionItem(
    name="check_dg2_stp_closed",
    description="Check that dg2 stopper is at closed switch.",
    pv="HFX:DG2:STP:01:CLOSE",
    value=1,
    operator=ConditionOperator.equal,
)
check_dg2_stp_not_open = ConditionItem(
    name="check_dg2_stp_not_open",
    description="Check that dg2 stopper is not at open switch.",
    pv="HFX:DG2:STP:01:OPEN",
    value=0,
    operator=ConditionOperator.equal,
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
    pfl_check = ConditionItem(
        name=f"check_pfl{index}_out",
        description="Check if lens is removed",
        pv=base_pv,
        value=0,
        operator=ConditionOperator.equal,
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
    tfs_check = ConditionItem(
        name=f"check_tfs{index}_out",
        description="Check if lens is removed",
        pv=base_pv,
        value=0,
        operator=ConditionOperator.equal,
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
    children=pfl_cads,
)

# Yags: insert
check_dg1_yag_in = ConditionItem(
    name="check_dg1_yag_in",
    description="Check if the dg1 yag is in",
    pv="MFX:DG1:PIM",
    value="YAG",
    operator=ConditionOperator.equal,
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
check_dg2_yag_in = ConditionItem(
    name="check_dg2_yag_in",
    description="Check if the dg2 yag is in",
    pv="MFX:DG2:PIM",
    value="YAG",
    operator=ConditionOperator.equal,
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
check_mfx_att_range = RangeConditionItem(
    name="check_mfx_att_range",
    description="Check if mfx_att is near 10% transmission",
    pv="MFX:ATT:COM:R_CUR",
    low_value=0.08,
    high_value=0.12,
)