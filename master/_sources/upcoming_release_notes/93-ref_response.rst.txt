93 ref_response
###############

API Breaks
----------
- N/A

Features
--------
- Implement Root node status and tip node (last ticked) in BehaviorTreeUpdateMessage.

Bugfixes
--------
- Adjust tree ticker service to interpret tick delay as ms, as advertised.
- Ensure TickStatus is always valid in
- Fix the `beams client get_heartbeat` command, which previously didn't pass
  its command name to the RPCClient properly

Maintenance
-----------
- Generally refine type hints and improve style.
- Adjust RPCClient to return last response in addition to stashing.
- Clean up some vestigial code.
- Add and improve tests that communicate between client and handler, adding useful
  fixtures and utilities for waiting for responses

Contributors
------------
- tangkong
