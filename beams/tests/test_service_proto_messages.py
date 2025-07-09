from uuid import uuid4

from google.protobuf.timestamp_pb2 import Timestamp

from beams.service.remote_calls.behavior_tree_pb2 import (
    BehaviorTreeUpdateMessage, NodeId, TickConfiguration, TickStatus)
from beams.service.remote_calls.command_pb2 import (AckNodeMessage,
                                                    CommandMessage,
                                                    CommandType,
                                                    LoadNewTreeMessage,
                                                    TickConfigurationMessage)
from beams.service.remote_calls.generic_message_pb2 import (GenericMessage,
                                                            MessageType)
from beams.service.remote_calls.heartbeat_pb2 import HeartBeatReply


class TestProtos:
    def test_generic(self, capsys):
        x = GenericMessage(mess_t=MessageType.MESSAGE_TYPE_HEARTBEAT)
        assert x.mess_t == MessageType.MESSAGE_TYPE_HEARTBEAT

    def test_behavior_tree_messages(self):
        y = BehaviorTreeUpdateMessage(
                mess_t=MessageType.MESSAGE_TYPE_BEHAVIOR_TREE_MESSAGE,
                tree_id=NodeId(name="CoolTree", uuid=str(uuid4())),
                node_id=NodeId(name="current_node", uuid=str(uuid4())),
                tick_status=TickStatus.RUNNING,
                tick_config=TickConfiguration.INTERACTIVE,
                tick_delay_ms=200
            )
        assert y.tree_id.name == "CoolTree"

    def test_heartbeat(self):
        tree1 = BehaviorTreeUpdateMessage(
            mess_t=MessageType.MESSAGE_TYPE_BEHAVIOR_TREE_MESSAGE,
            tree_id=NodeId(name="Tree1", uuid=str(uuid4())),
            node_id=NodeId(name="current_node", uuid=str(uuid4())),
            tick_status=TickStatus.RUNNING,
            tick_config=TickConfiguration.INTERACTIVE,
            tick_delay_ms=200
        )
        tree2 = BehaviorTreeUpdateMessage(
            mess_t=MessageType.MESSAGE_TYPE_BEHAVIOR_TREE_MESSAGE,
            tree_id=NodeId(name="Tree2", uuid=str(uuid4())),
            node_id=NodeId(name="current_node", uuid=str(uuid4())),
            tick_status=TickStatus.RUNNING,
            tick_config=TickConfiguration.INTERACTIVE,
            tick_delay_ms=200
        )
        # here we show packing multiple BT updates into the message
        z = HeartBeatReply(
                mess_t=MessageType.MESSAGE_TYPE_HEARTBEAT,
                reply_timestamp=Timestamp(),
                behavior_tree_update=[tree1, tree2]
        )

        # protobuf asserts order is maintained
        assert z.behavior_tree_update[0].tree_id.name == "Tree1"
        assert z.behavior_tree_update[1].tree_id.name == "Tree2"

    # can better test to show how optionals can be desrialized
    def test_command_message(self):
        com1 = CommandMessage(
                mess_t=MessageType.MESSAGE_TYPE_COMMAND_MESSAGE,
                command_t=CommandType.CHANGE_TICK_CONFIGURATION,
                tree_name="Tree1",
                tick_config=TickConfigurationMessage(tick_config=TickConfiguration.CONTINUOUS,
                                                     delay_ms=5)
            )
        lnt_mess = LoadNewTreeMessage(tree_file_path="beams/tests/artificats/eggs.json")
        lnt_mess.tick_spec.CopyFrom(TickConfigurationMessage(
            tick_config=TickConfiguration.CONTINUOUS,
            delay_ms=5
        ))
        com2 = CommandMessage(
            mess_t=MessageType.MESSAGE_TYPE_COMMAND_MESSAGE,
            command_t=CommandType.LOAD_NEW_TREE,
            tree_name="Tree2",
            load_new_tree=lnt_mess
        )

        ack_node_message = AckNodeMessage(
            node_name_to_ack="BigRedButton",
            user_acking_node="CoolestGuyInTown"
        )

        com3 = CommandMessage(
            mess_t=MessageType.MESSAGE_TYPE_COMMAND_MESSAGE,
            command_t=CommandType.ACK_NODE,
            tree_name="CoolTree"
        )
        com3.ack_node.CopyFrom(ack_node_message)

        assert com1.tree_name == "Tree1"
        assert not com2.HasField("ack_node")  # this is more useful in a strongly typed langauge but we should still leverage
        assert com3.ack_node.node_name_to_ack == "BigRedButton"

        # command_list = [com1, com2]
        # TODO finish this example in a more meaningful way
        # by showing how we can work through the command list and optionaly deserialize to change 'state
