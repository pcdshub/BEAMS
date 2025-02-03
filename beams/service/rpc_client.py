from __future__ import print_function

import argparse
import logging

import grpc

from beams.logging import setup_logging
from beams.service.remote_calls.generic_message_pb2 import MessageType, Empty
from beams.service.remote_calls.heartbeat_pb2 import HeartBeatReply
from beams.service.remote_calls.command_pb2 import (CommandType, CommandMessage,
                                                    LoadNewTreeMessage, AckNodeMessage, 
                                                    ChangeTickConfigurationMessage)

from beams.service.remote_calls.beams_rpc_pb2_grpc import BEAMS_rpcStub

logger = logging.getLogger(__name__)


def enumerate_choices(enum_type):
    return [e[0] for e in enum_type.items()]


def unwrap_protobuf_enum_wrapper(enum_type, enum_string_name):
    return dict(enum_type.items())[enum_string_name]


def parse_arguments():
    # arg parse and validation
    parser = argparse.ArgumentParser(
        prog="beams rpc client",
        description="allows users to interact with BEAMS service",
        epilog="I hope you're having as much fun as me",
    )

    subparsers = parser.add_subparsers(help="client subcommands")

    parser.add_argument(
        "-H",
        "--hbeat",
        help="get heartbeat message from service",
        action="store_true"
    )
    command_parser = subparsers.add_parser('command', 
                                           help="command parser help")
    command_parser.add_argument(
        '-c',
        "--command_type",
        type=str,
        choices=enumerate_choices(CommandType)
    )
    command_parser.add_argument(
        '-t',
        "--tree_name",
        type=str,
        help="name of tree to interact with"
    )
    # load new tree
    load_new_tree_parser = command_parser.add_argument_group(
                                    'load_new_tree', 
                                    "command for specifying new tree")
    load_new_tree_parser.add_argument(
        "-f",
        "--new_tree_filepath",
        help="filepath of tree to be loaded",
        type=str
    )
    load_new_tree_parser.add_argument(
        "-r",
        "--replace_existing_tree",
        help="If present will replace existing tree of sepcified name",
        type=str,
        default=""
    )

    # ack node
    ack_node_parser = command_parser.add_argument_group(
                                "ack_node",
                                "specify node to send use ack to")
    ack_node_parser.add_argument(
        "-n",
        '--node_name',
        type=str,
        help="name of node to acknowledge"
    )
    ack_node_parser.add_argument(
        "-t"
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

    return parser.parse_args()


class SequencerClient:
    def __init__(self, args):
        self.args = args

    def run(self):
        def p_message_info(mtype, mvalue):
            logger.debug(f"Sending message of type:({mtype}), value:({mvalue})")

        with grpc.insecure_channel(
            "localhost:50051"
        ) as channel:  # TODO: obviously not this. Grab from config
            stub = BEAMS_rpcStub(channel)
            response = None

            # build the message
            if self.args.hbeat:
                print("hbeat")
                response = stub.RequestHeartBeat(Empty())
            else:
                # unapack the command type from arg parse
                command_m = CommandMessage(mess_t=MessageType.MESSAGE_TYPE_COMMAND_MESSAGE)
                command_t = unwrap_protobuf_enum_wrapper(CommandType, self.args.command_type)
                command_m.command_t = command_t
                command_m.tree_name = self.args.tree_name

                # permutate state of running tree
                tree_execution_control_commands = [CommandType.PAUSE_TREE, CommandType.TICK_TREE, CommandType.START_TREE]

                # These commands only need captured tree name and command itself
                if command_t in tree_execution_control_commands + [CommandType.UNLOAD_TREE]:
                    pass
                elif command_t == CommandType.LOAD_NEW_TREE:
                    LNT_mess = LoadNewTreeMessage()
                    # should replace is true then
                    if self.args.replace_existing_tree != "":
                        LNT_mess.should_replace_existing_tree = True
                        LNT_mess.tree_to_replace = self.args.replace_existing_tree
                    else:
                        # in this case we will have the service just launch a new process for a new tree, forest in bound!!
                        LNT_mess.should_replace_existing_tree = False  # default but whatever
                    command_m.load_new_tree.CopyFrom(LNT_mess)
                # TODO other messages
                # elif command_t == MessageType.CHANGE_TICK_RATE_OF_TREE:
                #     change_tick_mess = ChangeTickConfigurationMessage()

                print(command_m)
                response = stub.EnqueueCommand(command_m)

            logger.debug(response)


if __name__ == "__main__":
    # TODO: determine what we want here.  Does it have its own logging
    # process and file?
    setup_logging(logging.DEBUG)
    args = parse_arguments()
    client = SequencerClient(args)
    client.run()
