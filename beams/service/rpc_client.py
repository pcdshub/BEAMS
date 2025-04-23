from __future__ import print_function

import logging
from functools import wraps
from typing import Optional

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
    BASE_COMMANDS: list[CommandType] = [
        CommandType.START_TREE,
        CommandType.TICK_TREE,
        CommandType.PAUSE_TREE,
        CommandType.UNLOAD_TREE,
    ]

    def __init__(self, *args, server_address: str = "localhost:50051", **kwargs):
        self.response = None
        self.server_address = server_address

    def run(self, command: str, **kwargs):
        def p_message_info(mtype, mvalue):
            logger.debug(f"Sending message of type:({mtype}), value:({mvalue})")

        if command.upper() == "GET_HEARTBEAT":
            self._get_heartbeat()
            logger.debug(self.response)
            return

        command = getattr(CommandType, command.upper())
        if command not in CommandType.values():
            raise ValueError(f"Unsupported command provided: {command}")

        # TODO: deal with none as tree name
        tree_name = kwargs.get("tree_name") or ""
        # These commands only need captured tree name and command itself
        if command in self.BASE_COMMANDS:
            getattr(self, CommandType.Name(command))(tree_name)
        elif command == CommandType.LOAD_NEW_TREE:
            self._load_new_tree(
                tree_name=tree_name,
                new_tree_filepath=kwargs["new_tree_filepath"],
                tick_config=kwargs["tick_mode"],
                tick_delay_ms=kwargs["tick_delay_ms"]
            )
        elif command == CommandType.LOAD_NEW_TREE:
            self._load_new_tree(
                tree_name=tree_name,
                new_tree_filepath=kwargs["new_tree_filepath"],
                tick_config=kwargs["tick_mode"],
                tick_delay_ms=kwargs["tick_delay_ms"],
            )
        elif command == CommandType.ACK_NODE:
            self._ack_node(
                tree_name=tree_name,
                node_name=kwargs["node_name"], user=kwargs["user"],
            )

        print(self.response)
        logger.debug(self.response)

    def construct_msg(self, command: CommandType, tree_name: str) -> CommandMessage:
        # unpack the command type from arg parse
        cmd_msg = CommandMessage(mess_t=MessageType.MESSAGE_TYPE_COMMAND_MESSAGE)
        cmd_msg.command_t = command
        cmd_msg.tree_name = tree_name
        return cmd_msg

    def with_server_stub(func):
        """
        Create rpc stub inside the grpc context as a decorator for commands
        If stub is provided, then the context already exists, run as normal
        """
        @wraps(func)
        def wrapper(self, *args, stub: Optional[BEAMS_rpcStub] = None, **kwargs):
            if not isinstance(self, RPCClient):
                raise ValueError("with_server_stub must decorate a method of "
                                 f"{type(RPCClient)}, not {type(self)}")

            if stub is None:
                # TODO: obviously not this. Grab from config
                with grpc.insecure_channel(self.server_address) as channel:
                    stub = BEAMS_rpcStub(channel)
                    return func(self, stub=stub, *args, **kwargs)
            else:
                return func(self, stub=stub, *args, **kwargs)

        return wrapper

    @with_server_stub
    def _get_heartbeat(self, stub: Optional[BEAMS_rpcStub] = None) -> None:
        self.response = stub.request_heartbeat(Empty())

    @with_server_stub
    def _start_tree(self, tree_name: str, stub: Optional[BEAMS_rpcStub] = None) -> None:
        cmd_msg = self.construct_msg(CommandType.START_TREE, tree_name)
        self.response = stub.enqueue_command(cmd_msg)

    @with_server_stub
    def _tick_tree(self, tree_name: str, stub: Optional[BEAMS_rpcStub] = None) -> None:
        cmd_msg = self.construct_msg(CommandType.TICK_TREE, tree_name)
        self.response = stub.enqueue_command(cmd_msg)

    @with_server_stub
    def _pause_tree(self, tree_name: str, stub: Optional[BEAMS_rpcStub] = None) -> None:
        cmd_msg = self.construct_msg(CommandType.PAUSE_TREE, tree_name)
        self.response = stub.enqueue_command(cmd_msg)

    @with_server_stub
    def _unload_tree(self, tree_name: str, stub: Optional[BEAMS_rpcStub] = None) -> None:
        cmd_msg = self.construct_msg(CommandType.UNLOAD_TREE, tree_name)
        self.response = stub.enqueue_command(cmd_msg)

    @with_server_stub
    def _load_new_tree(
        self,
        tree_name: str,
        new_tree_filepath: str,
        tick_config: str,
        tick_delay_ms: int,
        stub: Optional[BEAMS_rpcStub] = None,
    ) -> None:
        cmd_msg = self.construct_msg(CommandType.LOAD_NEW_TREE, tree_name)
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

    @with_server_stub
    def _ack_node(
        self,
        tree_name: str,
        node_name: str,
        user: str,
        stub: Optional[BEAMS_rpcStub] = None,
    ) -> None:
        cmd_msg = self.construct_msg(CommandType.ACK_NODE, tree_name)
        # TODO: grab user from kerberos?  Verify that user is who they say they are?
        ack_node_mess = AckNodeMessage(
            node_name_to_ack=node_name, user_acking_node=user
        )
        cmd_msg.ack_node.CopyFrom(ack_node_mess)

        # persist response
        self.response = stub.enqueue_command(cmd_msg)
