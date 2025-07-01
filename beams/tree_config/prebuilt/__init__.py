from beams.tree_config.prebuilt.reset_ioc import ResetIOCItem
from beams.tree_config.prebuilt.wait_for_ack import WaitForAckNodeItem

# Add items here if they should be made available in the GUI
_supported_items = [
    ResetIOCItem,
    WaitForAckNodeItem,
]
