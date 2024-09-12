import time
from modified_ljm import ljm
import multiprocessing as mp
from LabJackInterface import LabJack

#from SerialHandler import SerialDevices as sd, serial_thread
from ThreadManager import ThreadManager as tm
import datetime
counter = 0

def t8_callback(lji, data, db_workq):
    ff = lji.read_stream()
    db_workq.put(("T8", ff))
    global counter
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    print(timestamp, counter)

    counter += 1
    
    # print(timestamp, count)
    # count += 1
    # global counter
    # if counter == 100:
    #     timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    #     with open('output.txt', 'a') as file:
    #         file.write(f"Timestamp: {timestamp} ")
    #         file.write(f"Data: {ff}\n")
    #     counter = 0
    # counter += 1
    #print(ff)
    #db_workq.put(("T8", ff))
        
def t8_thread(db_workq):
    print("hello")
    '''
    Stream data from LabJack T8 and put it into the queue
    '''

    a_scan_list_names = ["AIN0", "AIN1", "AIN2", "AIN3", "AIN4", "AIN5", "AIN6", "AIN7"] 
    scan_rate = 1000  # Scan rate in Hz
    stream_resolution_index = 0 
    a_scan_list = ljm.namesToAddresses(len(a_scan_list_names), a_scan_list_names)[0]

    lji = LabJack("ANY", "USB", "ANY")    
    lji.start_stream(a_scan_list_names, scan_rate, scans_per_read=1, callback=t8_callback, obj = lji, workq = db_workq, stream_resolution_index= stream_resolution_index)
    #lji.start_stream(a_scan_list_names, scan_rate, scans_per_read=1, callback=None, obj = None, workq = None, stream_resolution_index= stream_resolution_index)
    while 1:
        time.sleep(0.1)
    