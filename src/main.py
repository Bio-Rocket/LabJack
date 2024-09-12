import multiprocessing as mp
from ThreadManager import ThreadManager as tm
from LabjackProcess import t7_pro_thread
import time
from DatabaseHandler import database_thread

def initialize_threads():
    '''
    Create threads for the backend
    '''
    thread_pool = {}

    t7_pro_workq= mp.Queue()
    db_workq = mp.Queue()
    pid_workq = mp.Queue()

    # Initialize the threads
    lj_t7_pro_thread = mp.Process(target=t7_pro_thread, args=(t7_pro_workq, db_workq))
    db_thread = mp.Process(target=database_thread, args=('database', db_workq))
    # pid_thread = mp.Process(target=pid_thread, args=(pid_workq,))

    # Add the threads to the thread pool
    thread_pool['T7_pro'] = {'thread': lj_t7_pro_thread, 'workq': t7_pro_workq}
    thread_pool['database'] = {'thread': db_thread, 'workq': db_workq}
    # thread_pool['pid'] = {'thread': pid_thread, 'workq': pid_workq}

    tm.thread_pool = thread_pool
    return

if __name__ == "__main__":
    tm()
    initialize_threads()
    tm.start_threads()
    while 1:
        time.sleep(1)
