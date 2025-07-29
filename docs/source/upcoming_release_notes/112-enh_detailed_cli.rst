112 enh_detailed_cli
#################

API Breaks
----------
- N/A

Features
--------
- Adds "get_tree_details" subcommand to CLI
- Adds uuid access options to CLI and Client.

Bugfixes
--------
- N/A

Maintenance
-----------
- Moves `BeamService` to `beams.service.rpc_handler`, to live with its other servicing friends
- Removes redundant SyncManager calls.  Don't need to register members to an already configured SyncManager
- Refactors tests to exercise multiple service interaction methods (both cli and client, name and uuid)

Contributors
------------
- tangkong
