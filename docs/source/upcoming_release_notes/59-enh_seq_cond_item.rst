59 enh_seq_cond_item
####################

API Breaks
----------
- Implicitly change the schema enough that the test json blobs needed to be regenerated.

Features
--------
- Add SequenceConditionItem, an item class that encodes a sequence that only contains
  BaseConditionItem sub-items. This is usable as a check for dataclasses that need a check.
- Add DummyConditionItem, a condition item for testing that always succeeds or always fails.
- Introduce BaseConditionItem and BaseSequenceItem as tagged unions for serialization.

Bugfixes
--------
- N/A

Maintenance
-----------
- Regenerate json eggs

Contributors
------------
- zllentz
