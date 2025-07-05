from collections import defaultdict
from dataclasses import dataclass
import time
from typing import Any, Callable, Dict, List
from br_threading.WorkQCommands import WorkQCmnd, WorkQCmnd_e
import multiprocessing as mp
from br_labjack.LabJackInterface import LabJack
from labjack.ljm import LJMError

LAB_JACK_SCAN_RATE = 1000 # Scan rate in Hz
DEFAULT_A_LIST_NAMES = ["AIN3", "AIN4", "AIN5", "AIN6", "AIN7", "AIN8", "AIN9", "AIN10", "AIN11", "AIN12", "AIN13"]
GET_SCANS_PER_READ = lambda x: int(x/2)

@dataclass
class LjData():
    scan_rate: int
    lc_data: Dict[str, list]
    pt_data: Dict[str, list]

class _CallbackClass:
    def __init__(self, lji: LabJack, workq_list: List[mp.Queue], scan_rate: int):
        """
        The callback class for the LabJack T7 Pro,
        including the labjack object to read from the stream and
        the list of threads that are subscribed to the labjack data.

        Args:
            lji (LabJack):
                The labjack object to read from the stream
            workq_list (List[mp.Queue]):
                The list of threads that are subscribed to the labjack data
            scan_rate (int):
                The scan rate in Hz
        """
        self.lji = lji
        self.subscribed_workq_list = workq_list
        self.scan_rate = scan_rate

def t7_pro_callback(obj: _CallbackClass, stream_handle: Any):
    """
    The callback function for the LabJack T7 Pro,
    for when the LabJack T7 Pro receives stream data.

    Args:
        obj (_CallbackClass): The callback class for the LabJack T7 Pro.
        stream_handle (Any): The stream handle for the LabJack T7 Pro.
    """
    ff = obj.lji.read_stream()

    scan_rate = obj.scan_rate
    lc_data = defaultdict(list)
    pt_data = defaultdict(list)

    for i in range(GET_SCANS_PER_READ(scan_rate)):
        data_arr = ff[0][i: i + 11] # for the 11 channels

        pt_data["PT12"].append(data_arr[0]) # AIN3
        pt_data["PT11"].append(data_arr[1]) # AIN4
        pt_data["PT10"].append(data_arr[2]) # AIN5
        pt_data["PT9"].append(data_arr[3]) # AIN6
        pt_data["PT8"].append(data_arr[4]) # AIN7
        pt_data["PT7"].append(data_arr[5]) # AIN8
        pt_data["PT6"].append(data_arr[6]) # AIN9

        lc_data["LC6"].append(data_arr[7]) # AIN10
        lc_data["LC5"].append(data_arr[8]) # AIN11
        lc_data["LC4"].append(data_arr[9]) # AIN12
        lc_data["LC3"].append(data_arr[10]) # AIN13


    cmnd = WorkQCmnd(WorkQCmnd_e.LJ_DATA, LjData(scan_rate, lc_data, pt_data))

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

def t7_pro_thread(
        t7_pro_workq: mp.Queue,
        db_workq: mp.Queue,
        scan_frequency: int = LAB_JACK_SCAN_RATE,
        a_scan_list: List[str] = DEFAULT_A_LIST_NAMES,
        labjack_stream_callback: Callable = t7_pro_callback):
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
        scan_frequency (int):
            The scan frequency in Hz. Default is 4 Hz.
        a_scan_list (List[str]):
            The list of AIN channels to stream from the LabJack T7 Pro.
            Default is ["AIN0", "AIN1", "AIN2", "AIN3", "AIN4", "AIN5", "AIN6", "AIN7", "AIN8", "AIN9", "AIN10"].
        labjack_stream_callback (function):
            !! IF USING A CUSTOM a_scan_list, YOU MUST PROVIDE A CUSTOM CALLBACK FUNCTION.
            The callback function for the LabJack T7 Pro,
            for when the LabJack T7 Pro receives stream data.
            Default is t7_pro_callback.
    """

    a_scan_list_names = a_scan_list
    scan_rate = scan_frequency
    stream_resolution_index = 0
    lji = None

    # Connect to the LabJack T7 Pro
    while lji is None:
        res, lji, err = connect_to_labjack()
        if not res:
            print(f"LJ - Error connecting to LabJack, {err}, retrying...")
            time.sleep(5)

    obj = _CallbackClass(lji, [db_workq,], scan_rate)

    lji.start_stream(a_scan_list_names, scan_rate, scans_per_read=GET_SCANS_PER_READ(scan_rate), callback=labjack_stream_callback, obj = obj, stream_resolution_index= stream_resolution_index)

    print("LJ - thread started")
    while 1:
        t7_pro_workq.get(block=True)
