import time
from labjack import ljm
import multiprocessing as mp
import LabJackInterface

from src.DatabaseHandler import database_thread
from src.SerialHandler import SerialDevices as sd, serial_thread
from src.ThreadManager import ThreadManager as tm

def t8_callback(lji, db_workq):
    data = lji.read_stream()
    db_workq.put("T8", data)
        
def t8_thread(db_workq, message_handler_workq):
    '''
    Stream data from LabJack T8 and put it into the queue
    '''

    a_scan_list_names = ["AIN0", "AIN1", "AIN2", "AIN3", "AIN4", "AIN5", "AIN6", "AIN7"] 
    scan_rate = 1000  # Scan rate in Hz
    stream_resolution_index = 0 
    a_scan_list = ljm.namesToAddresses(len(a_scan_list_names), a_scan_list_names)[0]

    lji = LabJackInterface("T8", "ANY", "ANY")
    lji.start_stream(a_scan_list_names, scan_rate, lambda: t8_callback(lji, db_workq), stream_resolution_index)