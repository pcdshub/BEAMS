"""
Communicate with a running BEAMS service (you are the client)

Provides subcommands for the following actions:
- get_heartbeat
- start_tree
- tick_tree
- pause_tree
- unload_tree
- load_tree
- change_tick_rate_of_tree
- change_tick_configuration
- ack_node
"""

import argparse
import logging

from beams.service.remote_calls.behavior_tree_pb2 import TickConfiguration

logger = logging.getLogger(__name__)

DESCRIPTION = __doc__


# subcommands here are identified by the same string as their CommandType enum
# aliases.  "True" command names are stored under the "commnand" default in each
# subparser
def build_arg_parser(argparser=None):
    if argparser is None:
        argparser = argparse.ArgumentParser()

    argparser.description = DESCRIPTION
    argparser.formatter_class = argparse.RawTextHelpFormatter

    subparsers = argparser.add_subparsers(
        help="client subcommands"
    )

    # get heartbeat
    sub = subparsers.add_parser("get_heartbeat")
    sub.set_defaults(command="get_heartbeat")

    # load new tree
    load_new_tree_parser = subparsers.add_parser(
        "load_new_tree",
        aliases=["LOAD_NEW_TREE", "load"],
        help="command for specifying new tree"
    )
    load_new_tree_parser.set_defaults(command="load_new_tree")
    load_new_tree_parser.add_argument(
        "new_tree_filepath",
        help="filepath of tree to be loaded",
        type=str
    )
    load_new_tree_parser.add_argument(
        "-m",
        "--tick_mode",
        type=str,
        choices=[mode for mode in TickConfiguration.keys()
                 if mode != "UNKNOWN"],
        default="CONTINUOUS",
        help="specify how the tree will be ticked"
    )
    load_new_tree_parser.add_argument(
        '-d',
        "--tick_delay_ms",
        help="specify tick delay (~period of ticking) in milliseconds",
        default=1000,
        type=int
    )

    # tick config
    tick_config_parser = subparsers.add_parser(
        "change_tick_configuration",
        aliases=["CHANGE_TICK_CONFIGURATION", "change_tick_cfg"],
        help="specify tick configuration"
    )
    tick_config_parser.set_defaults(command="change_tick_configuration")
    tick_config_parser.add_argument(
        "-m",
        "--tick_mode",
        type=str,
        choices=[mode for mode in TickConfiguration.keys()
                 if mode != "UNKNOWN"],
        default="CONTINUOUS",
        help="specify how the tree will be ticked"
    )
    tick_config_parser.add_argument(
        '-d',
        "--tick_delay_ms",
        help="specify tick delay (~period of ticking) in milliseconds",
        default=1000,
        type=int
    )

    # ack node
    ack_node_parser = subparsers.add_parser(
        "ack_node",
        aliases=["ACK_NODE"],
        help="specify node to send use ack to"
    )
    ack_node_parser.set_defaults(command="ack_node")
    ack_node_parser.add_argument(
        "-n",
        '--node_name',
        type=str,
        help="name of node to acknowledge",
        default="",
    )
    ack_node_parser.add_argument(
        "-u",
        "--user",
        type=str,
        help="user sending acknowledge",
        default="me"
    )

    # Basic parsers (only tree-name needed)
    start_parser = subparsers.add_parser(
        "start_tree",
        aliases=["START_TREE", "start"],
        help="Start a tree that has been loaded"
    )
    start_parser.set_defaults(command="start_tree")

    tick_parser = subparsers.add_parser(
        "tick_tree",
        aliases=["TICK_TREE", "tick"],
        help="Tick a running tree"
    )
    tick_parser.set_defaults(command="tick_tree")

    pause_parser = subparsers.add_parser(
        "pause_tree",
        aliases=["PAUSE_TREE", "pause"],
        help="Pause a running tree"
    )
    pause_parser.set_defaults(command="pause_tree")

    unload_parser = subparsers.add_parser(
        "unload_tree",
        aliases=["UNLOAD_TREE", "unload"],
        help="Unload a loaded tree"
    )
    unload_parser.set_defaults(command="unload_tree")

    # apply required tree identification arg for applicable subcommands
    for sub in [start_parser, load_new_tree_parser, tick_config_parser,
                ack_node_parser, pause_parser, tick_parser,
                unload_parser,]:
        sub.add_argument(
            "tree_name",
            type=str,
            help="name of tree to interact with (or load)"
        )

    return argparser


def main(*args, **kwargs):
    if kwargs["command"] is None:
        print("No command provided")
        return

    from beams.config import load_config
    from beams.service.rpc_client import RPCClient
    cmd = kwargs.pop("command")
    logger.debug(f"Executing {cmd} with args {args, kwargs}")
    client = RPCClient(config=load_config())
    client.run(cmd, *args, **kwargs)
