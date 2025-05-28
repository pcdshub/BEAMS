from __future__ import print_function

import configparser
import logging
import os
from functools import wraps
from pathlib import Path
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
from beams.service.remote_calls.heartbeat_pb2 import HeartBeatReply

logger = logging.getLogger(__name__)


class RPCClient:
    """Client for communicating with the BEAMS service via RPC"""
    BASE_COMMANDS: list[CommandType] = [
        CommandType.START_TREE,
        CommandType.TICK_TREE,
        CommandType.PAUSE_TREE,
        CommandType.UNLOAD_TREE,
    ]

    def __init__(
        self,
        address: str = "localhost",
        port: int = 50051,
    ):
        # Initialize with nonsense reply, techinically invalid
        self.last_response: HeartBeatReply = HeartBeatReply()
        self.server_address = f"{address}:{port}"

    @classmethod
    def from_config(cls, cfg: Optional[Path] = None):
        """
        Create a client from the configuration file specification.

        Configuration file should be of an "ini" format.  The accepted keys are:
        - server
            - address: str
            - port: int

        For example:

        .. code::

            [server]
            address = localhost
            port = 50051

        Parameters
        ----------
        cfg : Path, optional
            Path to the configuration file, by default None.  If omitted,
            :meth:`.find_config` will be used to find one.

        Raises
        ------
        RuntimeError
            If a configuration file cannot be found
        """
        if not cfg:
            cfg = cls.find_config()
        if not os.path.exists(cfg):
            raise RuntimeError(f"BEAMS configuration file not found: {cfg}")

        cfg_parser = configparser.ConfigParser()
        cfg_parser.read(cfg)
        logger.debug(f"Loading configuration file at ({cfg})")
        return cls.from_parsed_config(cfg_parser)

    @classmethod
    def from_parsed_config(
        cls,
        cfg_parser: configparser.ConfigParser,
    ):
        """
        Initializes Client using a ConfigParser that has already read in a config.
        This method enables the caller to edit a config after parsing but before
        Client initialization.
        """
        # server address information
        if "server" in cfg_parser.sections():
            server_address = cfg_parser["server"]["address"]
            server_port = int(cfg_parser["server"]["port"])
        else:
            logger.debug("No address information found")
            server_address = "localhost"
            server_port = 50051

        return cls(address=server_address, port=server_port)

    @staticmethod
    def find_config() -> Path:
        """
        Search for a ``beams`` configuation file.  Searches in the following
        locations in order
        - ``$BEAMS_CFG`` (a full path to a config file)
        - ``$XDG_CONFIG_HOME/{beams.cfg, .beams.cfg}`` (either filename)
        - ``~/.config/{beams.cfg, .beams.cfg}``

        Returns
        -------
        Path
            Absolute path to the configuration file

        Raises
        ------
        OSError
            If no configuration file can be found by the described methodology
        """
        # Point to with an environment variable
        env_path = os.environ.get('BEAMS_CFG', "")
        if env_path:
            logger.debug("Found $BEAMS_CFG specification for Client "
                         "configuration at %s", env_path)
            return Path(env_path).expanduser().resolve()
        # Search in the current directory and home directory
        else:
            config_dirs = [os.environ.get('XDG_CONFIG_HOME', "."),
                           os.path.expanduser('~/.config'),]
            for directory in config_dirs:
                logger.debug('Searching for beams config in %s', directory)
                for path in ('.beams.cfg', 'beams.cfg'):
                    full_path = os.path.join(directory, path)

                    if os.path.exists(full_path):
                        logger.debug("Found configuration file at %r", full_path)
                        return Path(full_path).expanduser().resolve()
        # If found nothing
        raise OSError("No beams configuration file found. Check BEAMS_CFG.")

    def run(self, command: str, **kwargs) -> HeartBeatReply:
        """
        Run a command

        `command` must be identical (sans capitalization) to the members of the
        CommandType Enum. (generated by protobuf)

        Extra information needed to execute the command should be provided as
        a keyword argument.

        Parameters
        ----------
        command : str
            the client command to run

        Raises
        ------
        ValueError
            If an unknown command is provided
        """
        if command.upper() == "GET_HEARTBEAT":
            self.get_heartbeat()
            logger.debug(self.last_response)
            return self.last_response

        command = getattr(CommandType, command.upper())
        if command not in CommandType.values():
            raise ValueError(f"Unsupported command provided: {command}")

        # TODO: deal with none as tree name
        tree_name = kwargs.get("tree_name") or ""
        # These commands only need captured tree name and command itself
        if command in self.BASE_COMMANDS:
            getattr(self, f"_{CommandType.Name(command).lower()}")(tree_name)
        elif command == CommandType.LOAD_NEW_TREE:
            self.load_new_tree(
                tree_name=tree_name,
                new_tree_filepath=kwargs["new_tree_filepath"],
                tick_config=kwargs["tick_mode"],
                tick_delay_ms=kwargs["tick_delay_ms"]
            )
        elif command == CommandType.ACK_NODE:
            self.ack_node(
                tree_name=tree_name,
                node_name=kwargs["node_name"], user=kwargs["user"],
            )

        logger.debug(self.last_response)
        return self.last_response

    def construct_base_msg(self, command: CommandType, tree_name: str) -> CommandMessage:
        """
        Construct the base CommandMessage for RPC communication.  Some command
        types may require additonal configuration of the message

        Parameters
        ----------
        command : CommandType
            The message subcommand type
        tree_name : str
            The name of the tree to manipulate

        Returns
        -------
        CommandMessage
        """
        # unpack the command type from arg parse
        cmd_msg = CommandMessage(mess_t=MessageType.MESSAGE_TYPE_COMMAND_MESSAGE)
        cmd_msg.command_t = command
        cmd_msg.tree_name = tree_name
        return cmd_msg

    @staticmethod
    def with_server_stub(func):
        """
        Create rpc stub inside the grpc context as a decorator for commands
        If stub is provided, then the context already exists, run as normal.
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
    def get_heartbeat(self, stub: Optional[BEAMS_rpcStub] = None) -> HeartBeatReply:
        """
        Get service heartbeat.  Currently this includes information on every
        tree running on the service.

        If `stub` is not provided, this will create one based on client settings

        Parameters
        ----------
        stub : Optional[BEAMS_rpcStub], optional
            the rpc stub used to send messages, by default None
        """
        self.last_response = stub.request_heartbeat(Empty())
        return self.last_response

    @with_server_stub
    def start_tree(
        self,
        tree_name: str,
        stub: Optional[BEAMS_rpcStub] = None
    ) -> HeartBeatReply:
        """
        Start the tree with `tree_name`.  The tree must already be loaded onto
        the service.

        If `stub` is not provided, this will create one based on client settings

        Parameters
        ----------
        tree_name : str
            the name of the tree to start
        stub : Optional[BEAMS_rpcStub], optional
            the rpc stub used to send messages, by default None
        """
        cmd_msg = self.construct_base_msg(CommandType.START_TREE, tree_name)
        self.last_response = stub.enqueue_command(cmd_msg)
        return self.last_response

    @with_server_stub
    def tick_tree(
        self,
        tree_name: str,
        stub: Optional[BEAMS_rpcStub] = None
    ) -> HeartBeatReply:
        """
        Tick the tree with `tree_name`.  The tree must already be loaded onto
        the service.

        If `stub` is not provided, this will create one based on client settings

        Parameters
        ----------
        tree_name : str
            the name of the tree to tick
        stub : Optional[BEAMS_rpcStub], optional
            the rpc stub used to send messages, by default None
        """
        cmd_msg = self.construct_base_msg(CommandType.TICK_TREE, tree_name)
        self.last_response = stub.enqueue_command(cmd_msg)
        return self.last_response

    @with_server_stub
    def pause_tree(
        self,
        tree_name: str,
        stub: Optional[BEAMS_rpcStub] = None
    ) -> HeartBeatReply:
        """
        Pause the tree with `tree_name`.  The tree must already be loaded onto
        the service.

        If `stub` is not provided, this will create one based on client settings

        Parameters
        ----------
        tree_name : str
            the name of the tree to pause
        stub : Optional[BEAMS_rpcStub], optional
            the rpc stub used to send messages, by default None
        """
        cmd_msg = self.construct_base_msg(CommandType.PAUSE_TREE, tree_name)
        self.last_response = stub.enqueue_command(cmd_msg)
        return self.last_response

    @with_server_stub
    def unload_tree(
        self,
        tree_name: str,
        stub: Optional[BEAMS_rpcStub] = None
    ) -> HeartBeatReply:
        """
        Unload the tree with `tree_name`.  The tree must already be loaded onto
        the service.

        If `stub` is not provided, this will create one based on client settings

        Parameters
        ----------
        tree_name : str
            the name of the tree to start
        stub : Optional[BEAMS_rpcStub], optional
            the rpc stub used to send messages, by default None
        """
        cmd_msg = self.construct_base_msg(CommandType.UNLOAD_TREE, tree_name)
        self.last_response = stub.enqueue_command(cmd_msg)
        return self.last_response

    @with_server_stub
    def load_new_tree(
        self,
        tree_name: str,
        new_tree_filepath: str,
        tick_config: str,
        tick_delay_ms: int,
        stub: Optional[BEAMS_rpcStub] = None,
    ) -> HeartBeatReply:
        """
        Load a new tree into the service.  Does not start the tree automatically.

        If `stub` is not provided, this will create one based on client settings

        Parameters
        ----------
        tree_name : str
            Name to identify the tree by
        new_tree_filepath : str
            Path to the serialized tree
        tick_config : str
            The tick mode (INTERACTIVE, CONTINUOUS)
        tick_delay_ms : int
            The delay between ticks in ms
        stub : Optional[BEAMS_rpcStub], optional
            the rpc stub used to send messages, by default None
        """
        cmd_msg = self.construct_base_msg(CommandType.LOAD_NEW_TREE, tree_name)
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
        self.last_response = stub.enqueue_command(cmd_msg)
        return self.last_response

    @with_server_stub
    def ack_node(
        self,
        tree_name: str,
        node_name: str,
        user: str,
        stub: Optional[BEAMS_rpcStub] = None,
    ) -> HeartBeatReply:
        """
        Acknowledge a node in a tree.

        If `stub` is not provided, this will create one based on client settings

        Parameters
        ----------
        tree_name : str
            Name of the tree holding node to acknowledge
        node_name : str
            Name of node being acknowledged
        user : str
            User name requesting acknowledgement
        stub : Optional[BEAMS_rpcStub], optional
            the rpc stub used to send messages, by default None

        Returns
        -------
        HeartBeatReply

        """
        cmd_msg = self.construct_base_msg(CommandType.ACK_NODE, tree_name)
        # TODO: grab user from kerberos?  Verify that user is who they say they are?
        ack_node_mess = AckNodeMessage(
            node_name_to_ack=node_name, user_acking_node=user
        )
        cmd_msg.ack_node.CopyFrom(ack_node_mess)

        # persist response
        self.last_response = stub.enqueue_command(cmd_msg)
        return self.last_response
