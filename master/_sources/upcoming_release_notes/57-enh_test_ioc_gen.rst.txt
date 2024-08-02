57 enh_test_ioc_gen
###################

API Breaks
----------
- N/A

Features
--------
- Add subcommand "beams gen_test_ioc", which can be used to generate a
  logic-free caproto IOC that mirrors a serialized json behavior tree's
  PVs.
  The expected usage is "beams gen_test_ioc my_bt.json > my_server.py".
  The resulting server file should be hand-edited to have the correct
  types and starting values. The server by default runs on non-standard
  port 5066 so that it can be used to test a real behavior tree as-is.

Bugfixes
--------
- N/A

Maintenance
-----------
- N/A

Contributors
------------
- zllentz
