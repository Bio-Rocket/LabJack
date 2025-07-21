from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
import time
from typing import Any, Callable, Dict, List
from br_threading.WorkQCommands import WorkQCmnd, WorkQCmnd_e
import multiprocessing as mp
from br_labjack.LabJackInterface import LabJack
from labjack.ljm import LJMError

CMD_RESPONSE_RATE_HZ = 5
CMD_RESPONSE_PERIOD = 1.0 / CMD_RESPONSE_RATE_HZ

STREAM_RATE_HZ = 1000 # Scan rate in Hz
DEFAULT_A_LIST_NAMES = ["AIN1", "AIN2", "AIN3", "AIN4", "AIN5", "AIN6", "AIN7", "AIN8", "AIN9", "AIN10", "AIN11", "AIN12", "AIN13"]
GET_SCANS_PER_READ = lambda x: int(x/2) if int(x/2) != 0 else 1


PT_MAP = {
    "AIN1": "PT14", "AIN2": "PT13", "AIN3": "PT12", "AIN4": "PT11",
    "AIN5": "PT10", "AIN6": "PT9",  "AIN7": "PT8",  "AIN8": "PT7",
    "AIN9": "PT6"
}
LC_MAP = {
    "AIN10": "LC6", "AIN11": "LC5", "AIN12": "LC4", "AIN13": "LC3"
}

class LJ_SCAN_MODE(Enum):
    SLOW = 0
    FAST = 1



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
        start_index = i * len(DEFAULT_A_LIST_NAMES)
        data_arr = ff[0][start_index: start_index + len(DEFAULT_A_LIST_NAMES)] # for the 11 channels

        pt_data["PT14"].append(data_arr[0]) # AIN1
        pt_data["PT13"].append(data_arr[1]) # AIN2
        pt_data["PT12"].append(data_arr[2]) # AIN3
        pt_data["PT11"].append(data_arr[3]) # AIN4
        pt_data["PT10"].append(data_arr[4]) # AIN5
        pt_data["PT9"].append(data_arr[5]) # AIN6
        pt_data["PT8"].append(data_arr[6]) # AIN7
        pt_data["PT7"].append(data_arr[7]) # AIN8
        pt_data["PT6"].append(data_arr[8]) # AIN9

        lc_data["LC6"].append(data_arr[9]) # AIN10
        lc_data["LC5"].append(data_arr[10]) # AIN11
        lc_data["LC4"].append(data_arr[11]) # AIN12
        lc_data["LC3"].append(data_arr[12]) # AIN13

    cmnd = WorkQCmnd(WorkQCmnd_e.LJ_DATA, LjData(scan_rate, lc_data, pt_data))

    for workq in obj.subscribed_workq_list:
        workq.put(cmnd)

def read_single_sample(
        lji: LabJack,
        a_scan_list: List[str],
        db_workq: mp.Queue,
        scan_frequency: int
    ):
    """
    Read a single sample from the LabJack T7 Pro.

    Args:
        lji (LabJack):
            The LabJack T7 Pro object to read from.
        a_scan_list (List[str]):
            The list of AIN channels to read from.
        db_workq (mp.Queue):
            The work queue for the database thread.
        scan_frequency (int):
            The scan frequency in Hz.
    """
    try:
        values = lji.read_names(a_scan_list)
    except LJMError as e:
        print(f"LJ - Command/Response read error: {e}")
        return

    pt_data = defaultdict(list)
    lc_data = defaultdict(list)

    for name, value in zip(a_scan_list, values):
        if name in PT_MAP:
            pt_data[PT_MAP[name]].append(value)
        elif name in LC_MAP:
            lc_data[LC_MAP[name]].append(value)

    cmnd = WorkQCmnd(WorkQCmnd_e.LJ_DATA, LjData(scan_frequency, lc_data, pt_data))
    db_workq.put(cmnd)

def connect_to_labjack():
    """
    Connect to the LabJack T7 Pro.

    Returns:
        res (bool): The result of the connection.
        LabJack: The LabJack T7 Pro object.
        err (str): The error message if the connection failed.
    """
    try:
        lji = LabJack("T7", "USB", "ANY")
    except LJMError as e:
        return False, None, str(e.errorString)
    return True, lji, ""

def t7_pro_thread(
        t7_pro_workq: mp.Queue,
        db_workq: mp.Queue,
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
        a_scan_list (List[str]):
            The list of AIN channels to stream from the LabJack T7 Pro.
            Default is DEFAULT_A_LIST_NAMES.
        labjack_stream_callback (function):
            !! IF USING A CUSTOM a_scan_list, YOU MUST PROVIDE A CUSTOM CALLBACK FUNCTION.
            The callback function for the LabJack T7 Pro,
            for when the LabJack T7 Pro receives stream data.
            Default is t7_pro_callback.
    """
    a_scan_list_names = a_scan_list
    stream_resolution_index = 4
    lji = None

    scan_mode = LJ_SCAN_MODE.SLOW

    # Connect to the LabJack T7 Pro
    while lji is None:
        res, lji, err = connect_to_labjack()
        if not res:
            print(f"LJ - Error connecting to LabJack, {err}, retrying...")
            time.sleep(5)

    print("LJ - thread started")

    stream_cb_obj = _CallbackClass(lji, [db_workq,], STREAM_RATE_HZ)

    while True:
        start = time.time()
        try:
            lj_command = t7_pro_workq.get(timeout=0.01)
        except:
            lj_command = None

        if lj_command is not None:
            if lj_command.command == WorkQCmnd_e.KILL_PROCESS:
                try:
                    lji.stop_stream()
                    lji.close()
                except:
                    pass
                print("LJ - thread stopped")
                return
            elif lj_command.command == WorkQCmnd_e.LJ_SLOW_LOGGING:
                print("LJ - Switching to slow logging")
                try:
                    lji.stop_stream()
                except:
                    pass
                scan_mode = LJ_SCAN_MODE.SLOW
            elif lj_command.command == WorkQCmnd_e.LJ_FAST_LOGGING:
                print("LJ - Switching to fast logging")
                scan_mode = LJ_SCAN_MODE.FAST
                lji.start_stream(
                    a_scan_list_names,
                    STREAM_RATE_HZ,
                    scans_per_read=GET_SCANS_PER_READ(STREAM_RATE_HZ),
                    callback=labjack_stream_callback,
                    obj=stream_cb_obj,
                    stream_resolution_index=stream_resolution_index
                )

        if scan_mode == LJ_SCAN_MODE.SLOW:
            # If in slow mode, read single samples
            read_single_sample(lji, a_scan_list_names, db_workq, CMD_RESPONSE_RATE_HZ)

        # CR rate
        elapsed = time.time() - start
        time.sleep(max(0, CMD_RESPONSE_PERIOD - elapsed))