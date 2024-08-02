29 fix-test-worker
#################

API Breaks
----------
- N/A

Features
--------
- N/A

Bugfixes
--------
- test_worker was failing non deterministically due to logically ungated work functions
- test_check_and_do was failing non deterministically due to lack of closed loop ticking

Maintenance
-----------
- N/A

Contributors
------------
- joshc-slac
