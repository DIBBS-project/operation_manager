import time
from threading import Thread
import logging
from models import Execution
import traceback

# Get an instance of a logger
logging.basicConfig(level=logging.INFO)


def check_operations():
    logging.info("checking operations")
    executions = Execution.objects.all()
    for execution in executions:

        if execution.operation_state in ["error", "finished"]:
            continue

        logging.info(execution.operation_state)
        logging.info(execution.get_operation_state_info())
        possible_transitions = filter(lambda x: x.to_state != "error", execution.get_operation_state_info().possible_transitions)
        logging.info(possible_transitions)

        if len(possible_transitions) > 0:
            # make the transition
            chosen_transition = possible_transitions[0]
            logging.info("doing the transition to %s" % (chosen_transition.get_name()))
            try:
                execution.get_operation_state_info().make_transition(chosen_transition.get_name())
            except Exception as e:
                traceback.print_exc()
                logging.error("recovering an error")


def periodic_checks():
    # Checking periodically operations
    while True:
        check_operations()
        time.sleep(10)

PERIODIC_THREAD = None


def create_periodic_check_thread():
    global PERIODIC_THREAD
    if PERIODIC_THREAD is None:
        PERIODIC_THREAD = Thread(target=periodic_checks, args=())
        PERIODIC_THREAD.start()
