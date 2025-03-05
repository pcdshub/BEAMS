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
    - beams.service.SequenceClient -> beams.sequenecer.client
    - beams.service.Sequencer -> beams.sequenecer.sequencer
    - beams.service.Server -> beams.sequenecer.server
    - beams.service.SequencerState -> beams.sequenecer.state
    - beams.service.helpers.SharedEnum -> beams.sequenecer.helpers.enum
    - beams.service.helpers.PriorityQueue -> beams.sequenecer.helpers.queue
    - beams.service.helpers.Timer -> beams.sequenecer.helpers.timer
    - beams.service.helpers.Worker -> beams.sequenecer.helpers.worker

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
