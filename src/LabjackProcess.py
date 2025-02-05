from dataclasses import dataclass
import time
from typing import Any, List
from br_threading.WorkQCommands import WorkQCmnd, WorkQCmnd_e
import multiprocessing as mp
from br_labjack.LabJackInterface import LabJack
from labjack.ljm import LJMError

LAB_JACK_SCAN_RATE = 4 # Scan rate in Hz

@dataclass
class LjData():
    lc_data: list
    pt_data: list

class _CallbackClass:
    def __init__(self, lji: LabJack, workq_list: List[mp.Queue]):
        """
        The callback class for the LabJack T7 Pro,
        including the labjack object to read from the stream and
        the list of threads that are subscribed to the labjack data.

        Args:
            lji (LabJack):
                The labjack object to read from the stream
            workq_list (List[mp.Queue]):
                The list of threads that are subscribed to the labjack data
        """
        self.lji = lji
        self.subscribed_workq_list = workq_list

def t7_pro_callback(obj: _CallbackClass, stream_handle: Any):
    """
    The callback function for the LabJack T7 Pro,
    for when the LabJack T7 Pro receives stream data.

    Args:
        obj (_CallbackClass): The callback class for the LabJack T7 Pro.
        stream_handle (Any): The stream handle for the LabJack T7 Pro.
    """
    ff = obj.lji.read_stream()
    data_arr = ff[0]

    lc_data = []
    pt_data = []

    lc_data.append(data_arr[0]) # LC3
    lc_data.append(data_arr[1]) # LC4
    lc_data.append(data_arr[2]) # LC5
    lc_data.append(data_arr[3]) # LC6

    pt_data.append(data_arr[4]) # PT6
    pt_data.append(data_arr[5]) # PT7
    pt_data.append(data_arr[6]) # PT8
    pt_data.append(data_arr[7]) # PT9
    pt_data.append(data_arr[8]) # PT10
    pt_data.append(data_arr[9]) # PT11
    pt_data.append(data_arr[10]) # PT12

    cmnd = WorkQCmnd(WorkQCmnd_e.LJ_DATA, LjData(lc_data, pt_data))

    for workq in obj.subscribed_workq_list:
        workq.put(cmnd)

def connect_to_labjack():
    """
    Connect to the LabJack T7 Pro.

    Returns:
        res (bool): The result of the connection.
        LabJack: The LabJack T7 Pro object.
        err (str): The error message if the connection failed.
    """
    try:
        lji = LabJack("ANY", "USB", "ANY")
    except LJMError as e:
        return False, None, str(e.errorString)
    return True, lji, ""

def t7_pro_thread(t7_pro_workq: mp.Queue, db_workq: mp.Queue):
    """
    Start the LabJack stream to stream sensor data to
    the database thread.

    Args:
        t7_pro_workq (mp.Queue):
            The work queue for the LabJack T7 Pro thread. Used
            for changing valve positions and other commands.
        db_workq (mp.Queue):
            The work queue for the database thread. Used for
            storing sensor data in the database.
    """

    a_scan_list_names = ["AIN0", "AIN1", "AIN2", "AIN3", "AIN4", "AIN5", "AIN6", "AIN7", "AIN8", "AIN9", "AIN10"]
    scan_rate = LAB_JACK_SCAN_RATE
    stream_resolution_index = 0
    lji = None

    # Connect to the LabJack T7 Pro
    while lji is None:
        res, lji, err = connect_to_labjack()
        if not res:
            print(f"LJ - Error connecting to LabJack, {err}, retrying...")
            time.sleep(5)

    obj = _CallbackClass(lji, [db_workq,])

    lji.start_stream(a_scan_list_names, scan_rate, scans_per_read=1, callback=t7_pro_callback, obj = obj, stream_resolution_index= stream_resolution_index)

    print("LJ - thread started")
    while 1:
        t7_pro_workq.get(block=True)
