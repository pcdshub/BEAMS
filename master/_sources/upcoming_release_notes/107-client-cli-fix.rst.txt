1 eggs
#################

API Breaks
----------
- N/A

Features
--------
- N/A

Bugfixes
--------
In beams/service/rpc_client.py we were faultily appending an `_` when searching for member tasks. This didn't get you when you were testing via shell and instantiating the class, but it does when you are purely using the cli interface.

Maintenance
-----------
- N/A

Contributors
------------
- N/A
