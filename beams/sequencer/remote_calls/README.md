# Remote Calls
We are using a GRPC server to structure RPC calls to our program.
Protobuf is a great industry standard for serializing data. This also obviates rolling our own TCP server and parsing bytes of the line. If ya got an issue with this contact Josh.

## Setup
* this should already be covered by installing `pip3 install requirements.txt` within your venv but: `python -m pip install grpcio-tools` is explicitly the package we want
* from top level Makefile you can run `make gen_grpc` to get build artifacts needed for runtime

## Structure
The "base" proto file is "generic_message.proto", each derived message type should (generally) get its own \[message_name].proto file. Here we have
* behavior_tree.proto - defines a message which contains information on the currently ticked tree
* heartbeat.proto - packages the BehaviorTreeUpdate messsage(s) into a HeartbeatReply message for clients
* command.proto - structure of expected commands requested of the program

### generic_message.proto
Serves as base module. Defines what type of fundamental messages this package intends to communicate with. 
The defined "GenericMessage" schema is very useful for strongly typed languages 
```
message GenericMessage {
  MessageType mess_t = 1;
}
```
and all derived messages should have MessageType mess_t as their first element and populated with the corresponding MessageType enum. In python this is less rigorously needed, but can suggest good behavior.

### behavior_tree.proto
A meaningful update to the behavior tree appears as follows (maybe ghub permalink to keep it tethered to code):
```
message BehaviorTreeUpdate {
  MessageType mess_t = 1; // MESSAGE_TYPE_BEHAVIOR_TREE_MESSAGE
  string tree_name = 2;
  string node_name = 3;
  TickStatus tick_status = 4;
  TickConfiguration tick_config= 5;
  int32 tick_delay_ms = 6;
}
```

### heartbeat.proto
Response to client
```
message HeartbeatReply {
  MessageType mess_t = 1;
  BehaviorTreeUpdate behavior_tree_update = 2; // when our program is ticking many trees this may become a repeated or mapped fields
  google.protobuf.Timestamp reply_timestamp = 3;
  // maybe program uptime and git hash??
}
```

### command.proto

