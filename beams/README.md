# BEAMS
## Directory Structure
### behavior_tree
Defines the lowest level elements that comrpise behavior trees. </br>
See [Behavior Trees in AI and Robotics](https://arxiv.org/pdf/\1709.00084.pdf) fore a *much* more in depth exploration of BTs.</br>
This implementation uses the [py_trees](https://py-trees.readthedocs.io/en/devel/) library.
###### Components
* Action Node : leaf node that launches action for execution
* Condition Node: leaf node that evaluates condition
* Check and Do: A composite node of Action and Condition joined by a Selector (fallback node in normal BT parlance). See section 3.1 of the aformentioned PDF for more info.
* Volatile Status: mechanism to make BT statuses processes safe in python
### sequencer
Defines sequencer engine that can be seen as the main object of this program. The sequencer will launch processes that handle remote procedure calls from clients, parse messages into trees that represent the explicit desired handling of requested command, and tick the tree itself.
This module uses [GRPC](https://grpc.io/) to facilitate RPC calls.
###### Components
* Sequencer : main object, launches child threads to field GRPC server, parse messages into trees, and tick ensuing trees
* SequenceServer : defines GRPC interactions
* SequenceClient : client to be launched in conjunction with main Sequencer object to inject RPC commands
* SequencerState : multiprocesses safe object to persist state variables needed for sequencing
* remote_calls
  * sequencer.proto : protofile definition for provided GRPC service
  * all other files are build artifacts, see top level Makefile
### tree_generator
Middleware that interfaces to low_level `behavior_tree` module. This uses the low level components to construct trees that field the sequences provided by this service. These trees are provided to the sequencer to be ticked.
* TreeGenerator : the meat of where request -> tree generation happens invocations to pyepics should happen here
