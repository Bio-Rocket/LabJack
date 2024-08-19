import time
from labjack import ljm
import multiprocessing as mp
import LabJackInterface

from src.DatabaseHandler import database_thread
from src.SerialHandler import SerialDevices as sd, serial_thread
from src.ThreadManager import ThreadManager as tm
from src.LabJackProcess import t8_thread

# Constants ========================================================================================


# Local Procedures ================================================================================
def initialize_threads():
        '''
        Create threads for the backend
        '''
        thread_pool = {}
        t7_workq = mp.Queue()
        t8_workq = mp.Queue()
        db_workq = mp.Queue()

        # Initialize the threads
        t7_thread = mp.Process(target=serial_thread, args=(t7_workq, db_workq))
        t8_thread = mp.Process(target=t8_thread, args=(t8_workq, db_workq))
        db_thread = mp.Process(target=database_thread, args=('database', db_workq))
        
        # Add the threads to the thread pool
        thread_pool['T7'] = {'thread': t7_thread, 'workq': t7_workq}
        thread_pool['T8'] = {'thread': t8_thread, 'workq': t8_workq}
        thread_pool['database'] = {'thread': db_thread, 'workq': db_workq}
        
        tm.thread_pool = thread_pool
        return

if __name__ == "__main__":
  tm()
  initialize_threads()
  tm.start_threads()

  while 1:
    tm.handle_thread_messages()