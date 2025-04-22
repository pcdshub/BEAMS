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


class RPCClient:
    TREE_CTRL_CMDS = [
        CommandType.PAUSE_TREE,
        CommandType.TICK_TREE,
        CommandType.START_TREE,
        CommandType.UNLOAD_TREE,
    ]

    def __init__(self, *args, **kwargs):
        self.response = None

    def run(self, command: str, **kwargs):
        def p_message_info(mtype, mvalue):
            logger.debug(f"Sending message of type:({mtype}), value:({mvalue})")

        command = command.upper()
        if command not in CommandType.keys() + ["GET_HEARTBEAT"]:
            raise ValueError(f"Unsupported command provided: {command}")

        with grpc.insecure_channel(
            "localhost:50051"
        ) as channel:  # TODO: obviously not this. Grab from config
            stub = BEAMS_rpcStub(channel)

            if command == "GET_HEARTBEAT":
                self._get_heartbeat(stub)
                logger.debug(self.response)
                return

            # TODO: deal with none as tree name
            cmd_msg = self.construct_msg(command, kwargs.get("tree_name") or "")

            # These commands only need captured tree name and command itself
            if cmd_msg.command_t in self.TREE_CTRL_CMDS:
                pass
            elif cmd_msg.command_t == CommandType.LOAD_NEW_TREE:
                self._load_new_tree(
                    stub, cmd_msg,
                    new_tree_filepath=kwargs["new_tree_filepath"],
                    tick_config=kwargs["tick_config"],
                    tick_delay_ms=kwargs["tick_delay_ms"],
                )
            elif cmd_msg.command_t == CommandType.ACK_NODE:
                self._ack_node(
                    stub, cmd_msg,
                    node_name=kwargs["node_name"], user=kwargs["user"],
                )

            logger.debug(self.response)

    def construct_msg(self, command: str, tree_name: str) -> CommandMessage:
        # unpack the command type from arg parse
        cmd_msg = CommandMessage(mess_t=MessageType.MESSAGE_TYPE_COMMAND_MESSAGE)
        cmd_type = getattr(CommandType, command)
        cmd_msg.command_t = cmd_type
        cmd_msg.tree_name = tree_name
        return cmd_msg

    def _get_heartbeat(self, stub: BEAMS_rpcStub) -> None:
        print("hbeat")
        self.response = stub.request_heartbeat(Empty())

    def _load_new_tree(
        self,
        stub: BEAMS_rpcStub,
        cmd_msg: CommandMessage,
        new_tree_filepath: str,
        tick_config: str,
        tick_delay_ms: int
    ) -> None:
        load_new_tree_mesg = LoadNewTreeMessage()
        load_new_tree_mesg.tree_file_path = new_tree_filepath
        # make tick config
        tc = TickConfigurationMessage()
        tc.tick_config = getattr(TickConfiguration, tick_config)
        tc.delay_ms = tick_delay_ms
        # pack em up
        load_new_tree_mesg.tick_spec.CopyFrom(tc)
        cmd_msg.load_new_tree.CopyFrom(load_new_tree_mesg)

        # persist response
        self.response = stub.enqueue_command(cmd_msg)

    def _ack_node(
        self,
        stub: BEAMS_rpcStub,
        cmd_msg: CommandMessage,
        node_name: str,
        user: str,
    ) -> None:
        # TODO: grab user from kerberos?  Verify that user is who they say they are?
        ack_node_mess = AckNodeMessage(
            node_name_to_ack=node_name, user_acking_node=user
        )
        cmd_msg.ack_node.CopyFrom(ack_node_mess)

        # persist response
        self.response = stub.enqueue_command(cmd_msg)
