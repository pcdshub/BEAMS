61 enh_check_and_do_more
########################

API Breaks
----------
- N/A

Features
--------
- Allow an action item's termination_check to be omitted if it will be used as the "do" in a ``CheckAndDoItem``.
  In these cases, the "check" node will be used as the termination check and a placeholder ``UseCheckConditionItem``
  will be included in the serialized data structure.

Bugfixes
--------
- N/A

Maintenance
-----------
- Modify the egg generator to use the ``UseCheckConditionItem`` and regenerate the test artifacts.

Contributors
------------
- zllentz
