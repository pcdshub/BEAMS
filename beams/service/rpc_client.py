from __future__ import print_function

import logging

import grpc

from beams.service.remote_calls.beams_rpc_pb2_grpc import BEAMS_rpcStub
from beams.service.remote_calls.behavior_tree_pb2 import TickConfiguration
from beams.service.remote_calls.command_pb2 import (AckNodeMessage,
                                                    CommandMessage,
                                                    CommandType,
                                                    LoadNewTreeMessage,
                                                    TickConfigurationMessage)
from beams.service.remote_calls.generic_message_pb2 import Empty, MessageType

logger = logging.getLogger(__name__)


def enumerate_choices(enum_type):
    return [e[0] for e in enum_type.items()]


def unwrap_protobuf_enum_wrapper(enum_type, enum_string_name):
    return dict(enum_type.items())[enum_string_name]


class RPCClient:
    def __init__(self):
        self.response = None

    def run(self, *args, **kwargs):
        def p_message_info(mtype, mvalue):
            logger.debug(f"Sending message of type:({mtype}), value:({mvalue})")

        with grpc.insecure_channel(
            "localhost:50051"
        ) as channel:  # TODO: obviously not this. Grab from config
            stub = BEAMS_rpcStub(channel)

            # build the message
            if args.hbeat:
                print("hbeat")
                self.response = stub.request_heartbeat(Empty())
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
                    load_new_tree_mesg = LoadNewTreeMessage()
                    load_new_tree_mesg.tree_file_path = self.args.new_tree_filepath
                    # make tick config
                    tc = TickConfigurationMessage()
                    tc.tick_config = unwrap_protobuf_enum_wrapper(TickConfiguration, self.args.tick_config)
                    tc.delay_ms = args.tick_delay_ms
                    # pack em up
                    load_new_tree_mesg.tick_spec.CopyFrom(tc)
                    command_m.load_new_tree.CopyFrom(load_new_tree_mesg)

                elif command_t == CommandType.ACK_NODE:
                    ack_node_mess = AckNodeMessage(
                                        node_name_to_ack=self.args.node_name,
                                        user_acking_node=self.args.user
                    )
                    command_m.ack_node.CopyFrom(ack_node_mess)
                print(command_m)
                self.response = stub.enqueue_command(command_m)

            logger.debug(self.response)
