from __future__ import print_function

import logging

import argparse

import grpc

from beams.sequencer.remote_calls.sequencer_pb2 import SequenceCommand, AlterState
from beams.sequencer.remote_calls.sequencer_pb2_grpc import SequencerStub
from beams.sequencer.remote_calls.sequencer_pb2 import SequenceType, RunStateType, MessageType, TickStatus


def enumerate_choices(enum_type):
  return [e[0] for e in enum_type.items()]


def parse_arguments():
  # arg parse and validation
  parser = argparse.ArgumentParser(
                    prog='sequencer client',
                    description='allows users to interact with sequencing server',
                    epilog="I hope you're having as much fun as me")

  group = parser.add_mutually_exclusive_group(required=True)  # only accept one of the following
  group.add_argument("-s", "--sequence", help="choose sequence", type=str, choices=enumerate_choices(SequenceType))
  group.add_argument("-S", "--priority_sequence", help="append sequence to top of queue", type=str, choices=enumerate_choices(SequenceType))
  group.add_argument("-r", "--run_state", help="change run state", type=str, choices=enumerate_choices(RunStateType))
  group.add_argument("-b", "--heartbeat", help="request_heartbeat", action='store_true')

  return parser.parse_args()


def run():
  args = parse_arguments()
  p_message_info = lambda mtype, mvalue : logging.debug(f"Sending messafe of type {mtype} of value {mvalue}")
  with grpc.insecure_channel('localhost:50051') as channel:
    stub = SequencerStub(channel)
    response = None
    if (args.run_state is not None):
      p_message_info(MessageType.MESSAGE_TYPE_ALTER_RUN_STATE, args.run_state)
      response = stub.ChangeRunState(AlterState(mess_t=MessageType.MESSAGE_TYPE_ALTER_RUN_STATE, stateToUpdateTo=args.run_state))
    elif (args.priority_sequence is not None):
      p_message_info(MessageType.MESSAGE_TYPE_ENQUEUE_SEQUENCE_PRIORITY, args.priority_sequence)
      response = stub.EnqueueSequence(SequenceCommand(mess_t=MessageType.MESSAGE_TYPE_ENQUEUE_SEQUENCE_PRIORITY, seq_t=args.priority_sequence))
    elif (args.sequence is not None):
      p_message_info(MessageType.MESSAGE_TYPE_ENQUEUE_SEQUENCE, args.sequence)
      response = stub.EnqueueSequence(SequenceCommand(mess_t=MessageType.MESSAGE_TYPE_ENQUEUE_SEQUENCE, seq_t=args.sequence))
    else:
      p_message_info("HEARTBEAT", "HEARTBEAT")
      response = stub.RequestHeartBeat()

    logging.debug(response)

if __name__ == "__main__":
  logging.basicConfig(level=logging.DEBUG)
  run()
