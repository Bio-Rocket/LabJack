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

TEST_DATABASE_SCHEMA = path.join(Path(__file__).parent, "valve_cycle_DatabaseSchema.json")

# ========== VARIABLES TO CHANGE DURING TESTING ==========

NUMBER_OF_CYCLES = 10
TIME_BETWEEN_CYCLES = 5

# ========================================================

if __name__ == "__main__":
    db_workq = mp.Queue()
    plc_workq = mp.Queue()
    state_workq = mp.Queue()
    t7_pro_workq = mp.Queue()

    labjack_scan_names = ["AIN0", "AIN1", "AIN2", "AIN3"]

    # Initialize the threads
    tm.create_thread(target=database_thread, args=(db_workq, state_workq, TEST_DATABASE_SCHEMA))
    tm.create_thread(target=plc_thread, args=(plc_workq, db_workq))
    tm.create_thread(target=state_thread, args=(state_workq, plc_workq, db_workq))

    tm.start_threads()
    for i in range(NUMBER_OF_CYCLES):
        state_workq.put(WorkQCmnd(WorkQCmnd_e.STATE_HANDLE_VALVE_COMMAND, "PBV1_CLOSE"))
        state_workq.put(WorkQCmnd(WorkQCmnd_e.STATE_HANDLE_VALVE_COMMAND, "PBV2_OPEN"))
        time.sleep(TIME_BETWEEN_CYCLES)

        state_workq.put(WorkQCmnd(WorkQCmnd_e.STATE_HANDLE_VALVE_COMMAND, "PBV1_OPEN"))
        state_workq.put(WorkQCmnd(WorkQCmnd_e.STATE_HANDLE_VALVE_COMMAND, "PBV2_CLOSE"))
        time.sleep(TIME_BETWEEN_CYCLES)


