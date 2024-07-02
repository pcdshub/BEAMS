from __future__ import print_function

import logging

import argparse

import grpc

from beams.sequencer.remote_calls.sequencer_pb2 import SequenceCommand, AlterState, GenericCommand, Empty
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


class SequencerClient():
  def __init__(self, args):
    self.args = args

  def run(self):
    p_message_info = lambda mtype, mvalue : logging.debug(f"Sending messafe of type {mtype} of value {mvalue}")
    with grpc.insecure_channel('localhost:50051') as channel:  # TODO: obviously not this. Grab from config
      stub = SequencerStub(channel)
      mt = None
      mess = None
      mess_val = None
      response = None

      if (self.args.run_state is not None):
        mt = MessageType.MESSAGE_TYPE_ALTER_RUN_STATE
        mess = args.run_state
        mess_val = GenericCommand(mess_t=mt, alt_m=AlterState(mess_t=mt, stateToUpdateTo=mess))
      elif (self.args.priority_sequence is not None):
        mt = MessageType.MESSAGE_TYPE_ENQUEUE_SEQUENCE_PRIORITY
        mess = args.priority_sequence
        mess_val = GenericCommand(mess_t=mt, seq_m=SequenceCommand(mess_t=mt, seq_t=mess))
      elif (self.args.sequence is not None):
        mt = MessageType.MESSAGE_TYPE_ENQUEUE_SEQUENCE
        mess = args.sequence
        print(f"Arg provided {args.sequence}")
        mess_val = GenericCommand(mess_t=mt, seq_m=SequenceCommand(mess_t=mt, seq_t=mess))

      if (mt is not None and mess is not None):
        p_message_info(mt, mess_val)
        response = stub.EnqueueCommand(mess_val)
      else:
        p_message_info("HEARTBEAT", "HEARTBEAT")
        response = stub.RequestHeartBeat(Empty())

      logging.debug(response)


if __name__ == "__main__":
  logging.basicConfig(level=logging.DEBUG)
  args = parse_arguments()
  client = SequencerClient(args)
  client.run()
