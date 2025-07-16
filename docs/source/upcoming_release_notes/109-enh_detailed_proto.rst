109 enh_detailed_proto
######################

API Breaks
----------
- N/A

Features
--------
- Adds the ability for the BEAMS service to provide detailed messages to a client, including the name, uuid, and status of every node in a tree
  - Adds `TreeDetails` proto message, which holds `NodeInfo`
  - Adds `NodeInfo`, a recursive message that details the node id, its status, and its childrens' `NodeInfo`
  - Adds code paths for the service to create and return these `TreeDetails` objects

- Adjusts the `RPCHandler` and `TreeTicker` to use UUIDs as the primary method of identifying trees
  - the "tree_dict" passed around is now keyed by a `TreeIdKey` object, which handles equality checks between both strings and uuids (in addition to its own type)
  - Ensures that the "name" used to identify the tree is the one the client provides, not the name specified in a tree config file
  - multiple trees that use the same config file can be loaded.  This will result in identical trees, each with a different UUID used to track it.


Bugfixes
--------
- N/A

Maintenance
-----------
- N/A

Contributors
------------
- tangkong
