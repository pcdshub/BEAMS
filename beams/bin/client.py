"""
Communicate with a running BEAMS service (you are the client)

Provides subcommands for the following actions:
- get_heartbeat
- start_tree
- tick_tree
- pause_tree
- unload_tree
- load_tree
- change_tick_rate
- change_tick_config
- ack_node
"""

import argparse
import logging

from beams.service.remote_calls.behavior_tree_pb2 import TickConfiguration

logger = logging.getLogger(__name__)

DESCRIPTION = __doc__


def build_arg_parser(argparser=None):
    if argparser is None:
        argparser = argparse.ArgumentParser()

    argparser.description = DESCRIPTION
    argparser.formatter_class = argparse.RawTextHelpFormatter

    argparser.add_argument(
        '-t',
        "--tree_name",
        type=str,
        help="name of tree to interact with"
    )

    subparsers = argparser.add_subparsers(
        help="client subcommands", dest="command"
    )

    # get heartbeat
    sub = subparsers.add_parser("get_heartbeat")

    # load new tree
    sub = subparsers.add_parser(
        "load_new_tree", help="command for specifying new tree"
    )
    sub.add_argument(
        "-f",
        "--new_tree_filepath",
        help="filepath of tree to be loaded",
        type=str
    )

    # tick config
    tick_config_parser = subparsers.add_parser(
        "tick_configuration", help="specify tick configuration"
    )
    tick_config_parser.add_argument(
        "-tc",
        "--tick_config",
        type=str,
        choices=TickConfiguration.keys(),
        help="specify how the tree will be ticked"
    )
    tick_config_parser.add_argument(
        '-d',
        "--tick_delay_ms",
        help="specify tick delay (~period of ticking) in milliseconds",
        type=int
    )

    # ack node
    ack_node_parser = subparsers.add_parser(
        "ack_node", help="specify node to send use ack to"
    )
    ack_node_parser.add_argument(
        "-n",
        '--node_name',
        type=str,
        help="name of node to acknowledge"
    )
    ack_node_parser.add_argument(
        "-t",
        "--tree_name",
        type=str,
        help="name of tree"
    )
    ack_node_parser.add_argument(
        "-u",
        "--user",
        type=str,
        help="user sending acknowledge"
    )

    # todo change tick config

    return argparser


def main(*args, **kwargs):
    if kwargs["command"] is None:
        print("No command provided")
        return

    from beams.service.rpc_client import RPCClient
    cmd = kwargs.pop("command")
    client = RPCClient()  # TODO: gather client from config
    client.run(cmd, *args, **kwargs)
