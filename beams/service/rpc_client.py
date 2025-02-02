from __future__ import print_function

import argparse
import logging

import grpc

from beams.logging import setup_logging
from beams.service.remote_calls.generic_message_pb2 import MessageType
from beams.service.remote_calls.heartbeat_pb2 import HeartbeatReply
from beams.service.remote_calls.command_pb2 import (CommandType, CommandMessage,
                                                    LoadNewTreeMessage, AckNodeMessage, 
                                                    ChangeTickConfigurationMessage)

from beams.service.remote_calls.beams_rpc_pb2_grpc import BEAMS_rpcStub

logger = logging.getLogger(__name__)


def enumerate_choices(enum_type):
    return [e[0] for e in enum_type.items()]


def parse_arguments():
    # arg parse and validation
    parser = argparse.ArgumentParser(
        prog="sequencer client",
        description="allows users to interact with sequencing server",
        epilog="I hope you're having as much fun as me",
    )

    group = parser.add_mutually_exclusive_group(
        required=True
    )  # only accept one of the following
    group.add_argument(
        "-s",
        "--sequence",
        help="choose sequence",
        type=str,
        choices=enumerate_choices(SequenceType),
    )
    group.add_argument(
        "-S",
        "--priority_sequence",
        help="append sequence to top of queue",
        type=str,
        choices=enumerate_choices(SequenceType),
    )
    group.add_argument(
        "-r",
        "--run_state",
        help="change run state",
        type=str,
        choices=enumerate_choices(RunStateType),
    )
    group.add_argument(
        "-b", "--heartbeat", help="request_heartbeat", action="store_true"
    )

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
            mt = None
            mess = None
            mess_val = None
            response = None

            if self.args.run_state is not None:
                mt = MessageType.MESSAGE_TYPE_ALTER_RUN_STATE
                mess = args.run_state
                mess_val = GenericCommand(
                    mess_t=mt, alt_m=AlterState(mess_t=mt, stateToUpdateTo=mess)
                )
            elif self.args.priority_sequence is not None:
                mt = MessageType.MESSAGE_TYPE_ENQUEUE_SEQUENCE_PRIORITY
                mess = args.priority_sequence
                mess_val = GenericCommand(
                    mess_t=mt, seq_m=SequenceCommand(mess_t=mt, seq_t=mess)
                )
            elif self.args.sequence is not None:
                mt = MessageType.MESSAGE_TYPE_ENQUEUE_SEQUENCE
                mess = args.sequence
                logger.debug(f"Arg provided {args.sequence}")
                mess_val = GenericCommand(
                    mess_t=mt, seq_m=SequenceCommand(mess_t=mt, seq_t=mess)
                )

            if mt is not None and mess is not None:
                p_message_info(mt, mess_val)
                response = stub.EnqueueCommand(mess_val)
            else:
                p_message_info("HEARTBEAT", "HEARTBEAT")
                response = stub.RequestHeartBeat(Empty())

            logger.debug(response)


if __name__ == "__main__":
    # TODO: determine what we want here.  Does it have its own logging
    # process and file?
    setup_logging(logging.DEBUG)
    args = parse_arguments()
    client = SequencerClient(args)
    client.run()
