import multiprocessing as mp
from ThreadManager import ThreadManager as tm
from LabjackProcess import t8_thread
import time
from DatabaseHandler import database_thread

def initialize_threads():
    '''
    Create threads for the backend
    '''
    thread_pool = {}
    t8_workq = mp.Queue()
    db_workq = mp.Queue()

    # Initialize the threads
    lj_t8_thread = mp.Process(target=t8_thread, args=(db_workq,))
    db_thread = mp.Process(target=database_thread, args=('database', db_workq))
    # Add the threads to the thread pool
    thread_pool['T8'] = {'thread': lj_t8_thread, 'workq': t8_workq}
    thread_pool['database'] = {'thread': db_thread, 'workq': db_workq}
    tm.thread_pool = thread_pool
    return

if __name__ == "__main__":
    tm()
    initialize_threads()
    tm.start_threads()
    while 1:
        time.sleep(1)
    #   tm.handle_thread_messages()
