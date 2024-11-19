71 doc_unify_logging
####################

API Breaks
----------
- Renames modules to abide by PEP8 standards
    - beams.behavior_tree.ActionNode -> beams.behavior_tree.action_node
    - beams.behavior_tree.ActionWorker -> beams.behavior_tree.action_worker
    - beams.behavior_tree.CheckAndDo -> beams.behavior_tree.check_and_do
    - beams.behavior_tree.ConditionNode -> beams.behavior_tree.condition_node
    - beams.behavior_tree.VolatileStatus -> beams.behavior_tree.volatile_status
    - beams.sequencer.SequenceClient -> beams.sequenecer.client
    - beams.sequencer.Sequencer -> beams.sequenecer.sequencer
    - beams.sequencer.Server -> beams.sequenecer.server
    - beams.sequencer.SequencerState -> beams.sequenecer.state
    - beams.sequencer.helpers.SharedEnum -> beams.sequenecer.helpers.enum
    - beams.sequencer.helpers.PriorityQueue -> beams.sequenecer.helpers.queue
    - beams.sequencer.helpers.Timer -> beams.sequenecer.helpers.timer
    - beams.sequencer.helpers.Worker -> beams.sequenecer.helpers.worker

Features
--------
- N/A

Bugfixes
--------
- N/A

Maintenance
-----------
- Unify logging message format, with the intent of differentiating parent and child processes
- Nitpick some Multiprocessing object type hints

Contributors
------------
- tangkong
