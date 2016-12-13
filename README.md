# Operation Manager

## Execution FSM (Finite State Machine)

The execution of an operation is implemented as a FSM (Finite State Machine), which the states defined in this file:
https://github.com/DIBBS-project/operation_manager/blob/development/omapp/fsm/fsm.py

The following diagram illustrates an execution:
![alt text](docs/states.png "States of an execution")

### Implementation of the transitions

The transition between states of the FSM have been implemented in the following file:
https://github.com/DIBBS-project/operation_manager/blob/development/omapp/core.py

Here is a summary of how a specific transition is implemented:

| Transition    | Method                     |
| ------------- |:--------------------------:| 
| Deploying     | mark_deploying_handler     | 
| Bootstrapping | mark_bootstrapping_handler | 
| Configuring   | mark_configuring_handler   | 
| Executing     | mark_executing_handler     |
| Collecting    | mark_collecting_handler    |
| Finishing     | mark_finishing_handler     |
