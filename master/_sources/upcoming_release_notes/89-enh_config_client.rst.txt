89 enh_config_client
####################

API Breaks
----------
- N/A

Features
--------
- N/A

Bugfixes
--------
- N/A

Maintenance
-----------
- Add config file loading functionality to RPCClient.
  Searches the following locations in order for a config file:
  - ``$BEAMS_CFG`` (a full path to a config file)
  - ``$XDG_CONFIG_HOME/{beams.cfg, .beams.cfg}`` (either filename)
  - ``~/.config/{beams.cfg, .beams.cfg}``

Contributors
------------
- tangkong
