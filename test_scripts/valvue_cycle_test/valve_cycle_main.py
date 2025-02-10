from collections import defaultdict
import multiprocessing as mp
from pathlib import Path
import sys
import time
import os.path as path
from typing import Any

sys.path.append(path.join(Path(__file__).parents[2].as_posix(), "src/"))

from StateMachine import state_thread
from br_threading.WorkQCommands import WorkQCmnd, WorkQCmnd_e
from PlcHandler import plc_thread
from valve_cycle_DatabaseHandler import database_thread
from br_threading.ThreadManager import ThreadManager as tm
from LabjackProcess import GET_SCANS_PER_READ, _CallbackClass, LjData, t7_pro_thread

TEST_DATABASE_SCHEMA = path.join(Path(__file__).parent, "valve_cycle_DatabaseSchema.json")
VALVE_CYCLE_LJ_FREQ = 4 # Hz

# ========== VARIABLES TO CHANGE DURING TESTING ==========

NUMBER_OF_CYCLES = 10
TIME_BETWEEN_CYCLES = 5

# ========================================================

def valve_cycle_lj_callback(obj: _CallbackClass, _: Any):
    """
    SPECIFIC CALLBACK FUNCTION FOR PT PU TEST

    The callback function for the LabJack T7 Pro,
    for when the LabJack T7 Pro receives stream data.

    Args:
        obj (_CallbackClass): The callback class for the LabJack T7 Pro.
        _ (Any): The stream handle for the LabJack T7 Pro.
    """
    ff = obj.lji.read_stream()

    scan_rate = obj.scan_rate
    pt_data = defaultdict(list)

    for i in range(GET_SCANS_PER_READ(scan_rate)):
        data_arr = ff[0][i: i + 4] # for the 4 channels

        pt_data["PT1"].append(data_arr[0])
        pt_data["PT2"].append(data_arr[1])
        pt_data["PT3"].append(data_arr[2])
        pt_data["PT4"].append(data_arr[3])

    cmnd = WorkQCmnd(WorkQCmnd_e.LJ_DATA, LjData(obj.scan_rate, {}, pt_data))

    for workq in obj.subscribed_workq_list:
        workq.put(cmnd)

if __name__ == "__main__":
    db_workq = mp.Queue()
    plc_workq = mp.Queue()
    state_workq = mp.Queue()
    t7_pro_workq = mp.Queue()

    labjack_scan_names = ["AIN0", "AIN1", "AIN2", "AIN3"]

    # Initialize the threads
    tm.create_thread(target=database_thread, args=(db_workq, state_workq, TEST_DATABASE_SCHEMA))
    tm.create_thread(target=t7_pro_thread, args=(t7_pro_workq, db_workq, VALVE_CYCLE_LJ_FREQ, labjack_scan_names, valve_cycle_lj_callback))
    tm.create_thread(target=plc_thread, args=(plc_workq, db_workq))
    tm.create_thread(target=state_thread, args=(state_workq, plc_workq, db_workq))

    tm.start_threads()
    while 1:
        for i in range(NUMBER_OF_CYCLES):
            state_workq.put(WorkQCmnd(WorkQCmnd_e.STATE_HANDLE_VALVE_COMMAND, "HEATER_OFF"))
            state_workq.put(WorkQCmnd(WorkQCmnd_e.STATE_HANDLE_VALVE_COMMAND, "PUMP3_ON"))
            time.sleep(TIME_BETWEEN_CYCLES)

            state_workq.put(WorkQCmnd(WorkQCmnd_e.STATE_HANDLE_VALVE_COMMAND, "HEATER_ON"))
            state_workq.put(WorkQCmnd(WorkQCmnd_e.STATE_HANDLE_VALVE_COMMAND, "PUMP3_OFF"))
            time.sleep(TIME_BETWEEN_CYCLES)


