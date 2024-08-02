99 mnt_paused_heartbeat
#######################

API Breaks
----------
- N/A

Features
--------
- Adds a TreeStatus enum to be delivered in the BehaviorTreeUpdateMessages, which reports the meta status of the tree as one of:

  - `IDLE`
  - `RUNNING`
  - `WAITING_ACK`
  - `ERROR`

Bugfixes
--------
- N/A

Maintenance
-----------
- N/A

Contributors
------------
- tangkong
