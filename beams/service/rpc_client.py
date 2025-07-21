from __future__ import print_function

import configparser
import logging
import os
from functools import wraps
from pathlib import Path
from typing import Optional, Union
from uuid import UUID

import grpc

from beams.service.remote_calls.beams_rpc_pb2_grpc import BEAMS_rpcStub
from beams.service.remote_calls.behavior_tree_pb2 import (NodeId,
                                                          TickConfiguration,
                                                          TreeDetails)
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
            return Path(env_path)
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
                        return Path(full_path)
        # If found nothing
        raise OSError("No beams configuration file found. Check BEAMS_CFG.")

    def run(self, command: str, **kwargs) -> Union[HeartBeatReply, TreeDetails]:
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
            response = self.get_heartbeat()
            return response

        # TODO: deal with none as tree name
        tree_name = kwargs.get("tree_name") or ""
        tree_uuid = kwargs.get("tree_uuid") or ""
        # These commands only need captured tree name and command itself
        if command.upper() == "GET_TREE_DETAILS":
            response = self.get_detailed_update(tree_name=tree_name, tree_uuid=tree_uuid)
            return response

        command = getattr(CommandType, command.upper())
        if command not in CommandType.values():
            raise ValueError(f"Unsupported command provided: {command}")

        if command in self.BASE_COMMANDS:
            cmd_method = getattr(self, f"{CommandType.Name(command).lower()}")
            cmd_method(tree_name=tree_name, tree_uuid=tree_uuid)
        elif command == CommandType.LOAD_NEW_TREE:
            self.load_new_tree(
                tree_name=tree_name,
                tree_uuid=tree_uuid,
                new_tree_filepath=kwargs["new_tree_filepath"],
                tick_config=kwargs["tick_mode"],
                tick_delay_ms=kwargs["tick_delay_ms"]
            )
        elif command == CommandType.ACK_NODE:
            self.ack_node(
                tree_name=tree_name,
                node_name=kwargs["node_name"], user=kwargs["user"],
            )

        return self.last_response

    def construct_base_msg(
        self,
        command: CommandType,
        tree_name: str,
        tree_uuid: str,
    ) -> CommandMessage:
        """
        Construct the base CommandMessage for RPC communication.  Some command
        types may require additonal configuration of the message

        Parameters
        ----------
        command : CommandType
            The message subcommand type
        tree_name : str
            The name of the tree to manipulate
        tree_uuid : str
            The uuid of the tree to manipulate

        Returns
        -------
        CommandMessage
        """
        # unpack the command type from arg parse
        cmd_msg = CommandMessage(mess_t=MessageType.MESSAGE_TYPE_COMMAND_MESSAGE)
        cmd_msg.command_t = command
        cmd_msg.tree_name = tree_name
        cmd_msg.tree_uuid = tree_uuid
        return cmd_msg

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
                with grpc.insecure_channel(
                    self.server_address,
                    # Default ecs config uses psproxy, which doesn't work here
                    options=(("grpc.enable_http_proxy", 0),)
                ) as channel:
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
        logger.debug(self.last_response)
        return self.last_response

    @with_server_stub
    def start_tree(
        self,
        tree_name: str = "",
        tree_uuid: str = "",
        stub: Optional[BEAMS_rpcStub] = None
    ) -> HeartBeatReply:
        """
        Start the tree by specifying either its `tree_name` or `tree_uuid`.
        The tree must already be loaded onto the service.

        If `stub` is not provided, this will create one based on client settings

        Parameters
        ----------
        tree_name : str
            the name of the tree to start
        tree_uuid : str
            the uuid of the tree to start
        stub : Optional[BEAMS_rpcStub], optional
            the rpc stub used to send messages, by default None
        """
        if not (tree_name or tree_uuid):
            raise ValueError("Must provide either tree_name or tree_uuid")

        cmd_msg = self.construct_base_msg(CommandType.START_TREE, tree_name, tree_uuid)
        self.last_response = stub.enqueue_command(cmd_msg)
        logger.debug(self.last_response)
        return self.last_response

    @with_server_stub
    def tick_tree(
        self,
        tree_name: str = "",
        tree_uuid: str = "",
        stub: Optional[BEAMS_rpcStub] = None
    ) -> HeartBeatReply:
        """
        Tick the tree by specifying either its `tree_name` or `tree_uuid`.
        The tree must already be loaded onto the service.

        If `stub` is not provided, this will create one based on client settings

        Parameters
        ----------
        tree_name : str
            the name of the tree to tick
        tree_uuid : str
            the uuid of the tree to start
        stub : Optional[BEAMS_rpcStub], optional
            the rpc stub used to send messages, by default None
        """
        if not (tree_name or tree_uuid):
            raise ValueError("Must provide either tree_name or tree_uuid")

        cmd_msg = self.construct_base_msg(CommandType.TICK_TREE, tree_name, tree_uuid)
        self.last_response = stub.enqueue_command(cmd_msg)
        logger.debug(self.last_response)
        return self.last_response

    @with_server_stub
    def pause_tree(
        self,
        tree_name: str = "",
        tree_uuid: str = "",
        stub: Optional[BEAMS_rpcStub] = None
    ) -> HeartBeatReply:
        """
        Pause the tree by specifying either its `tree_name` or `tree_uuid`.
        The tree must already be loaded onto the service.

        If `stub` is not provided, this will create one based on client settings

        Parameters
        ----------
        tree_name : str
            the name of the tree to pause
        tree_uuid : str
            the uuid of the tree to start
        stub : Optional[BEAMS_rpcStub], optional
            the rpc stub used to send messages, by default None
        """
        if not (tree_name or tree_uuid):
            raise ValueError("Must provide either tree_name or tree_uuid")

        cmd_msg = self.construct_base_msg(CommandType.PAUSE_TREE, tree_name, tree_uuid)
        self.last_response = stub.enqueue_command(cmd_msg)
        logger.debug(self.last_response)
        return self.last_response

    @with_server_stub
    def unload_tree(
        self,
        tree_name: str = "",
        tree_uuid: str = "",
        stub: Optional[BEAMS_rpcStub] = None
    ) -> HeartBeatReply:
        """
        Unload the tree by specifying either its `tree_name` or `tree_uuid`.
        The tree must already be loaded onto the service.

        If `stub` is not provided, this will create one based on client settings

        Parameters
        ----------
        tree_name : str
            the name of the tree to start
        tree_uuid : str
            the uuid of the tree to start
        stub : Optional[BEAMS_rpcStub], optional
            the rpc stub used to send messages, by default None
        """
        if not (tree_name or tree_uuid):
            raise ValueError("Must provide either tree_name or tree_uuid")

        cmd_msg = self.construct_base_msg(CommandType.UNLOAD_TREE, tree_name, tree_uuid)
        self.last_response = stub.enqueue_command(cmd_msg)
        logger.debug(self.last_response)
        return self.last_response

    @with_server_stub
    def load_new_tree(
        self,
        new_tree_filepath: str,
        tree_name: str = "",
        tree_uuid: str = "",
        tick_config: str = "INTERACTIVE",
        tick_delay_ms: int = 5000,
        stub: Optional[BEAMS_rpcStub] = None,
    ) -> HeartBeatReply:
        """
        Load a new tree into the service.  Does not start the tree automatically.
        One of `tree_name` or `tree_uuid` must be provided

        If `stub` is not provided, this will create one based on client settings

        Parameters
        ----------
        tree_name : str
            Name to identify the tree by
        tree_uuid: str
            UUID to identify tree by
        new_tree_filepath : str
            Path to the serialized tree
        tick_config : str, optional
            The tick mode (INTERACTIVE, CONTINUOUS), by default INTERACTIVE
        tick_delay_ms : int, optional
            The delay between ticks in ms, by default 5000 (5s)
        stub : Optional[BEAMS_rpcStub], optional
            the rpc stub used to send messages, by default None
        """
        if not (tree_name or tree_uuid):
            raise ValueError("Must provide either tree_name or tree_uuid")

        cmd_msg = self.construct_base_msg(CommandType.LOAD_NEW_TREE, tree_name, tree_uuid)
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
        logger.debug(self.last_response)
        return self.last_response

    @with_server_stub
    def ack_node(
        self,
        node_name: str,
        user: str,
        tree_name: str = "",
        tree_uuid: str = "",
        stub: Optional[BEAMS_rpcStub] = None,
    ) -> HeartBeatReply:
        """
        Acknowledge a node in a tree specified by either its name or uuid

        If `stub` is not provided, this will create one based on client settings

        Parameters
        ----------
        tree_name : str
            Name of the tree holding node to acknowledge
        tree_uuid: str
            UUID of the tree holding node to acknowledge
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
        if not (tree_name or tree_uuid):
            raise ValueError("Must provide either tree_name or tree_uuid")

        cmd_msg = self.construct_base_msg(CommandType.ACK_NODE, tree_name, tree_uuid)
        # TODO: grab user from kerberos?  Verify that user is who they say they are?
        ack_node_mess = AckNodeMessage(
            node_name_to_ack=node_name, user_acking_node=user
        )
        cmd_msg.ack_node.CopyFrom(ack_node_mess)

        # persist response
        self.last_response = stub.enqueue_command(cmd_msg)
        logger.debug(self.last_response)
        return self.last_response

    def get_detailed_update(
        self,
        tree_name: Optional[str] = None,
        tree_uuid: Optional[Union[UUID, str]] = "",
        stub: Optional[BEAMS_rpcStub] = None,
    ) -> TreeDetails:
        """
        Gets a detailed update for a tree from the service.
        Trees can be identified by either their name or uuid, but at least one
        of these must be provided.

        If the uuid is provided, the tree name is ignored.

        Parameters
        ----------
        tree_name : Optional[str]
            The name of the tree in question
        tree_uuid : Optional[Union[UUID, str]]
            The uuid of the tree in question.  May be a partial uuid (>= 5 characters)
        stub : Optional[BEAMS_rpcStub], optional
            the rpc stub used to send messages, by default None

        Returns
        -------
        TreeDetails
            a detailed view of the tree
        """
        if not (tree_name or tree_uuid):
            raise ValueError("Must provide either tree_name or tree_uuid")

        tree_id = NodeId(name=tree_name, uuid=str(tree_uuid))
        if stub is None:
            # TODO: obviously not this. Grab from config
            with grpc.insecure_channel(self.server_address) as channel:
                stub = BEAMS_rpcStub(channel)
                resp = stub.request_tree_details(tree_id)
        else:
            resp = stub.request_tree_details(tree_id)

        self.last_response = resp
        return resp
