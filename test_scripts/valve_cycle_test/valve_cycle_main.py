import multiprocessing as mp
from pathlib import Path
import sys
import time
import os.path as path

sys.path.append(path.join(Path(__file__).parents[2].as_posix(), "src/"))

from StateMachine import state_thread
from br_threading.WorkQCommands import WorkQCmnd, WorkQCmnd_e
from PlcHandler import plc_thread
from valve_cycle_DatabaseHandler import database_thread
from br_threading.ThreadManager import ThreadManager as tm

TEST_DATABASE_SCHEMA = path.join(Path(__file__).parent, "valve_cycle_DatabaseSchema.json")

# Main ========================================================

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python valve_cycle_main.py <num_cycles> <wait_between_cycles>")
        sys.exit(1)

    try:
        num_cycles = int(sys.argv[1])
        wait_between_cycles = int(sys.argv[2])
    except ValueError:
        print("Both arguments must be integers.")
        sys.exit(1)

    db_workq = mp.Queue()
    plc_workq = mp.Queue()
    state_workq = mp.Queue()
    t7_pro_workq = mp.Queue()

    # Initialize the threads
    tm.create_thread(target=database_thread, args=(db_workq, state_workq, TEST_DATABASE_SCHEMA))
    tm.create_thread(target=plc_thread, args=(plc_workq, db_workq))
    tm.create_thread(target=state_thread, args=(state_workq, plc_workq, db_workq))

    tm.start_threads()
    for i in range(num_cycles):
        state_workq.put(WorkQCmnd(WorkQCmnd_e.STATE_HANDLE_VALVE_COMMAND, "PBV1_CLOSE"))
        state_workq.put(WorkQCmnd(WorkQCmnd_e.STATE_HANDLE_VALVE_COMMAND, "PBV2_OPEN"))
        time.sleep(wait_between_cycles)

        state_workq.put(WorkQCmnd(WorkQCmnd_e.STATE_HANDLE_VALVE_COMMAND, "PBV1_OPEN"))
        state_workq.put(WorkQCmnd(WorkQCmnd_e.STATE_HANDLE_VALVE_COMMAND, "PBV2_CLOSE"))
        time.sleep(wait_between_cycles)


