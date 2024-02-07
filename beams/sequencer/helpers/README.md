# Sequencing Helpers
Various helper classes oriented around distributing work or sharing variables in a multiproccesing friendly manner

## Worker
* An base class for child classes whos main function is to support a work thread.
* Holds volatile `self.do_work` which is intended to handle kill signal
* Provides `start_work` and `stop_work` functions to spawn and stop work processes 
* Optional constructor arg `stop_func` to be executde on process termination before joining work process.

## SharedEnum
Utility that wraps enum and allows it to be stored in the standard shared Value() type.

## SharedCommandReply
Utility that wraps the data intended for a protobuf CommandReply packet such that all entities can be updated in a threadsage manner