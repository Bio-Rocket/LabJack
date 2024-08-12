import time
from labjack import ljm
import multiprocessing as mp

from src.DatabaseHandler import database_thread
from src.SerialHandler import SerialDevices as sd, serial_thread
from src.ThreadManager import ThreadManager as tm

# Constants ========================================================================================

T7_IP = "192.168.0.0"
T8_IP = "192.168.0.1"

# Local Procedures ================================================================================
def initialize_threads():
        '''
        Create threads for the backend
        '''
        thread_pool = {}
        t7_workq = mp.Queue()
        t8_workq = mp.Queue()
        db_workq = mp.Queue()
        message_handler_workq = mp.Queue()

        # Create a main thread for handling thread messages
        thread_pool['message_handler'] = {'thread': None, 'workq': message_handler_workq}

        # Initialize the threads
        t7_thread = mp.Process(target=serial_thread, args=('t7', sd.UART, T7_IP, t7_workq, message_handler_workq))
        t8_thread = mp.Process(target=t8_thread, args=(T8_IP, t8_workq, message_handler_workq))
        db_thread = mp.Process(target=database_thread, args=('database', db_workq, message_handler_workq))
        
        # Add the threads to the thread pool
        thread_pool['uart'] = {'thread': t7_thread, 'workq': t7_workq}
        thread_pool['radio'] = {'thread': t8_thread, 'workq': t8_workq}
        thread_pool['database'] = {'thread': db_thread, 'workq': db_workq}
        
        tm.thread_pool = thread_pool
        return

def labjack_stream_thread(IP, t8_workq, message_handler_workq):
    '''
    Stream data from LabJack T8 and put it into the queue
    '''
    handle = ljm.openS("T8", "ANY", "ANY")  # Open the first found T8 device
    scan_rate = 1000  # Scan rate in Hz
    scans_per_read = scan_rate // 2  # Number of scans per read

    # Stream configuration
    a_scan_list_names = ["AIN0", "AIN1"] 
    a_scan_list = ljm.namesToAddresses(len(a_scan_list_names), a_scan_list_names)[0]

    # Configure and start stream
    ljm.eWriteNames(handle, len(a_scan_list_names), a_scan_list_names, [0.0] * len(a_scan_list_names))
    ljm.eStreamStart(handle, scans_per_read, len(a_scan_list), a_scan_list, scan_rate)

    try:
        while True:
            results = ljm.eStreamRead(handle)
            data = results
            t8_workq.put(data)
            time.sleep(.1)
    except KeyboardInterrupt:
        pass
    finally:
        ljm.eStreamStop(handle)
        ljm.close(handle)

if __name__ == "__main__":
  tm()
  initialize_threads()
  tm.start_threads()

  while 1:
    tm.handle_thread_messages()