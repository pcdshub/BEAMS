import logging
import time
from concurrent import futures
from dataclasses import dataclass, field
from multiprocessing import Queue, Semaphore
from multiprocessing.managers import BaseManager
from typing import Dict, List, Optional, Tuple, Union
from uuid import UUID, uuid4

import grpc

from beams.service.helpers.worker import Worker
from beams.service.remote_calls.beams_rpc_pb2_grpc import (
    BEAMS_rpcServicer, add_BEAMS_rpcServicer_to_server)
from beams.service.remote_calls.behavior_tree_pb2 import (
    BehaviorTreeUpdateMessage, NodeId, TreeDetails)
from beams.service.remote_calls.command_pb2 import CommandMessage
from beams.service.remote_calls.generic_message_pb2 import MessageType
from beams.service.remote_calls.heartbeat_pb2 import HeartBeatReply
from beams.service.tree_ticker import TreeTicker

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TreeIdKey:
    """
    Tree ID information bundle.

    Name exists for readability only, and all comparisons are made on the uuid.
    Partial uuids (str) matching the beginning of an instance's uuid are
    considered equal to the instance (for ease of matching)

    Note that this does not let you use partial strings to match dictionary keys
    via the `in` keyword, since __contains__ uses hashes
    """
    name: str
    uuid: UUID = field(default_factory=uuid4)

    def __hash__(self) -> int:
        # allow quick lookups by specifying uuid
        return hash(self.uuid)

    def __eq__(self, other) -> bool:
        # Require partial strings to be greater than 5 to avoid collisions
        # Eventually maybe somebody does some stats to figure out what a good
        # threshold is (birthday paradox)
        if isinstance(other, str):
            if len(other) >= 5:
                uuid_match = str(self.uuid).startswith(other)
            else:
                uuid_match = False
            name_match = (self.name == other)
            return uuid_match or name_match
        elif isinstance(other, UUID):
            return self.uuid == other
        elif isinstance(other, TreeIdKey):
            return self.uuid == other.uuid
        return False


TreeTickerDict = Dict[TreeIdKey, TreeTicker]


def get_tree_from_treetickerdict(
    tree_dict: TreeTickerDict,
    name: Optional[str] = None,
    uuid: Optional[Union[UUID, str]] = None,
) -> Union[Tuple[TreeIdKey, TreeTicker], Tuple[None, None]]:
    """
    Returns TreeIdKey and TreeTicker from `tree_dict` to best effort.
    In order of priority:
    1. Check for uuid full match
    2. Check for uuid partial match
    3. Check for tree name full match

    Returns the first match it finds, in the case of collisions
    Returns None if no match can be found
    """
    # `tree_dict` is often actually a multiprocessing.BaseProxy, which only exposes
    # methods, not attributes (or subscripting).  Also, the way we use this
    # the values of the dictionary are frequently AutoProxy[TreeTicker],
    # which cannot be checked for identity against itself.
    # So in the end we do this the slow and silly way
    if not (name or uuid):
        raise ValueError("One of `name` and `uuid` must be provided")

    if isinstance(uuid, str) and len(uuid) < 5 and uuid != "":
        raise ValueError("Partial uuids must provide at least "
                         f"5 characters, got ({uuid})")

    for key, value in tree_dict.items():
        # covers partial uuids, full uuids (string or object)
        if key == uuid:
            return key, value
        elif key == name:
            return key, value

    return None, None


class RPCHandler(BEAMS_rpcServicer, Worker):
    def __init__(self, sync_manager: BaseManager, port=50051):
        # GRPC server launching things from docs:
        # https://grpc.io/docs/languages/python/basics/#starting-the-server
        self.thread_pool = futures.ThreadPoolExecutor(max_workers=10)
        self.server = grpc.server(self.thread_pool)
        self.server_port = port

        # calling Worker's super
        super().__init__(proc_name="RPCHandler",
                         stop_func=lambda: self.server.stop(1),
                         grace_window_before_terminate_seconds=.5)

        self.sync_man = sync_manager
        if sync_manager is not None:  # for testing modularity purposes
            # process safe dictionary given by BEAMSService so we can appropriately respond with heartbeat
            logger.debug(f"Connecting to sync_man at: {self.sync_man.address}")
            self.sync_man.connect()
            # do these need to be here? the manager will have these registered already
            self.sync_man.register("get_tree_dict")
            self.sync_man.register("TreeTicker")
            self.sync_man.register("TreeState")

        # queue for owning object to grab commands s
        self.incoming_command_queue = Queue()
        self.command_ready_sem = Semaphore(value=0)

    # NOTE: these could also live and work in a process spawned by beams service..
    # returns a single bt update as a list...
    def attempt_to_get_tree_update(
        self,
        tree_name: Optional[str] = None,
        tree_uuid: Optional[Union[UUID, str]] = None,
    ) -> Optional[List[BehaviorTreeUpdateMessage]]:
        if self.sync_man is None:  # for testing modularity
            return None
        with self.sync_man as man:
            tree_dict: TreeTickerDict = man.get_tree_dict()
            key, tree_ticker = get_tree_from_treetickerdict(
                tree_dict, name=tree_name, uuid=tree_uuid
            )
            if key and tree_ticker:
                update = tree_ticker.get_behavior_tree_update()
                # replace tree_id with information that can identify tree in service
                return [BehaviorTreeUpdateMessage(
                    mess_t=update.mess_t,
                    tree_id=NodeId(name=key.name, uuid=str(key.uuid)),
                    node_id=update.node_id,
                    tick_status=update.tick_status,
                    tick_config=update.tick_config,
                    tick_delay_ms=update.tick_delay_ms,
                    tree_status=update.tree_status,

                )]
            else:
                logger.error(f"Unable to find tree of name {tree_name} currently being ticked")
                return None

    def get_all_tree_updates(self) -> Optional[List[BehaviorTreeUpdateMessage]]:
        if self.sync_man is None:  # for testing modularity
            return None

        with self.sync_man as man:
            tree_dict: TreeTickerDict = man.get_tree_dict()
            # if dictionary empty return none
            if len(tree_dict.items()) == 0:
                return None

            updates = []
            for key, tree_ticker in tree_dict.items():
                update = tree_ticker.get_behavior_tree_update()
                update_msg = BehaviorTreeUpdateMessage(
                    mess_t=update.mess_t,
                    tree_id=NodeId(name=key.name, uuid=str(key.uuid)),
                    node_id=update.node_id,
                    tick_status=update.tick_status,
                    tick_config=update.tick_config,
                    tick_delay_ms=update.tick_delay_ms,
                    tree_status=update.tree_status,
                )
                updates.append(update_msg)

            return updates

    def enqueue_command(self, request: CommandMessage, context) -> HeartBeatReply:
        mess_t = request.mess_t
        if mess_t != MessageType.MESSAGE_TYPE_COMMAND_MESSAGE:
            logger.error("You seriously messed up, reevlauate your life choices")
        else:
            self.incoming_command_queue.put(request)
            logger.debug(f"Command of type: {request.command_t} enqueued for {request.tree_name}")
            self.command_ready_sem.release()

        bt_update = None
        if self.sync_man is not None:  # for testing modularity
            bt_update = self.attempt_to_get_tree_update(request.tree_name)

        hbeat_message = HeartBeatReply(mess_t=MessageType.MESSAGE_TYPE_HEARTBEAT)
        hbeat_message.reply_timestamp.GetCurrentTime()

        if bt_update is None:
            return hbeat_message
        else:
            hbeat_message.behavior_tree_update.extend(bt_update)
            return hbeat_message

    def request_heartbeat(self, request, context) -> HeartBeatReply:
        # assumption that hitting this service endpoint means you want to know
        # ALL the trees this service is currently ticking

        # TODO: it is placing like here that I am not happy with the distance
        # of the py_trees vs GRPC object, reflect on this
        # for example: how could we keep thee py_tree treename and this one aligned?
        updates = self.get_all_tree_updates()

        hbeat_message = HeartBeatReply(mess_t=MessageType.MESSAGE_TYPE_HEARTBEAT)
        hbeat_message.reply_timestamp.GetCurrentTime()

        if updates is None:
            return hbeat_message
        else:
            hbeat_message.behavior_tree_update.extend(updates)
            return hbeat_message

    def request_tree_details(self, request: NodeId, context) -> Optional[TreeDetails]:
        """
        Gather tree details for the node ID provided

        Parameters
        ----------
        request : NodeId
            The identification

        Returns
        -------
        TreeDetails
            The details of the requested tree
        """
        with self.sync_man as manager:
            tree_dict: TreeTickerDict = manager.get_tree_dict()
            key, tree_ticker = get_tree_from_treetickerdict(tree_dict, request.name,
                                                            request.uuid)
            if tree_ticker and key:
                details = tree_ticker.get_detailed_update()

                # repackage into new message with the right details
                new_details = TreeDetails(
                    tree_id=NodeId(name=key.name, uuid=str(key.uuid)),
                    node_info=details.node_info,
                    tree_status=details.tree_status,
                )
                return new_details

            return TreeDetails()

    def work_func(self):
        logger.debug(f"{self.proc_name} running")
        add_BEAMS_rpcServicer_to_server(self, self.server)
        self.server.add_insecure_port(f"[::]:{self.server_port}")  # note: binding to localhost implicitly
        self.server.start()
        logger.debug("Server started, listening on " + str(self.server_port))
        while self.do_work.value:
            time.sleep(0.1)
        logger.debug("RPCHandler work_func exitted")
