116 enh_client_config
#####################

API Breaks
----------
- N/A

Features
--------
- Implement a basic config file for specifying which port for the server to use
  and which host:port for the client to use.

Bugfixes
--------
- N/A

Maintenance
-----------
- Tweak the log messages to reflect that we have configurable host:port combinations.
- Add ``make grpc`` as an alias for ``make gen_grpc``

Contributors
------------
- zllentz
