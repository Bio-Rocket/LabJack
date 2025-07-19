import multiprocessing as mp
from StateTruth import StateTruth, SystemStates
from br_threading.ThreadManager import ThreadManager as tm
import time

from DatabaseHandler import database_thread
from PlcHandler import plc_thread
from LabjackProcess import t7_pro_thread
from StateMachine import state_thread
from HeartbeatHandler import heartbeat_thread

def process_wrapper(func, shared_dict, *args):
    # Set up shared state in all the subprocess
    StateTruth.init_state_truth(shared_dict)
    func(*args)

if __name__ == "__main__":
    manager = mp.Manager()
    shared_state = manager.dict({"state": SystemStates.ABORT})
    #TODO: this will need updated for embedded mode
    StateTruth.init_state_truth(shared_state)

    #TODO SHOULD GET STATE FROM DB IF IT EXISTS

    db_workq = mp.Queue()
    plc_workq = mp.Queue()
    t7_pro_workq = mp.Queue()
    state_workq = mp.Queue()
    heartbeat_workq = mp.Queue()

    # Initialize the threads
    tm.create_thread(
        target=process_wrapper,
        args=(database_thread, shared_state, db_workq, state_workq, heartbeat_workq)
    )
    tm.create_thread(
        target=process_wrapper,
        args=(t7_pro_thread, shared_state, t7_pro_workq, db_workq)
    )
    tm.create_thread(
        target=process_wrapper,
        args=(plc_thread, shared_state, plc_workq, db_workq)
    )
    tm.create_thread(
        target=process_wrapper,
        args=(state_thread, shared_state, state_workq, plc_workq, db_workq)
    )
    tm.create_thread(
        target=process_wrapper,
        args=(heartbeat_thread, shared_state, heartbeat_workq, db_workq, state_workq)
    )


    tm.start_threads()
    while 1:
        time.sleep(1)
