from collections import defaultdict
import multiprocessing as mp
from pathlib import Path
import sys
import time
import os.path as path
from typing import Any


sys.path.append(path.join(Path(__file__).parents[2].as_posix(), "src/"))

from br_threading.WorkQCommands import WorkQCmnd, WorkQCmnd_e
from pt_pu_DatabaseHandler import database_thread
from br_threading.ThreadManager import ThreadManager as tm
from LabjackProcess import GET_SCANS_PER_READ, _CallbackClass, LjData, t7_pro_thread

TEST_DATABASE_SCHEMA = path.join(Path(__file__).parent, "pt_pu_DatabaseSchema.json")
PT_PU_LJ_FREQ = 500 # Hz

def pt_pu_lj_callback(obj: _CallbackClass, stream_handle: Any):
    """
    SPECIFIC CALLBACK FUNCTION FOR PT PU TEST

    The callback function for the LabJack T7 Pro,
    for when the LabJack T7 Pro receives stream data.

    Args:
        obj (_CallbackClass): The callback class for the LabJack T7 Pro.
        stream_handle (Any): The stream handle for the LabJack T7 Pro.
    """
    ff = obj.lji.read_stream()
    data_arr = ff[0]

    scan_rate = obj.scan_rate
    pt_data = defaultdict(list)

    for i in range(GET_SCANS_PER_READ(scan_rate)):
        pt_data["PT1"].append(data_arr[0]) # PT1 raw voltage
        pt_data["PU1"].append(data_arr[1]) # PU1

    cmnd = WorkQCmnd(WorkQCmnd_e.LJ_DATA, LjData(obj.scan_rate, {}, pt_data))

    for workq in obj.subscribed_workq_list:
        workq.put(cmnd)


if __name__ == "__main__":
    db_workq = mp.Queue()
    t7_pro_workq = mp.Queue()
    state_workq = mp.Queue() # need for db to not crash out in case of state request, but not used

    labjack_scan_names = ["AIN0", "AIN1"]

    # Initialize the threads
    tm.create_thread(target=database_thread, args=(db_workq, TEST_DATABASE_SCHEMA))
    tm.create_thread(target=t7_pro_thread, args=(t7_pro_workq, db_workq, PT_PU_LJ_FREQ, labjack_scan_names, pt_pu_lj_callback))

    tm.start_threads()
    while 1:
        time.sleep(1)
