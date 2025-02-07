import multiprocessing as mp
from pathlib import Path
import sys
import time
import os.path as path


sys.path.append(path.join(Path(__file__).parents[2].as_posix(), "src/"))

from pt_pu_DatabaseHandler import database_thread
from br_threading.ThreadManager import ThreadManager as tm
from LabjackProcess import t7_pro_thread

TEST_DATABASE_SCHEMA = path.join(Path(__file__).parent, "pt_pu_DatabaseSchema.json")

if __name__ == "__main__":
    db_workq = mp.Queue()
    t7_pro_workq = mp.Queue()
    state_workq = mp.Queue() # need for db to not crash out in case of state request, but not used

    labjack_scan_names = ["AIN0", "AIN1"]

    # Initialize the threads
    tm.create_thread(target=database_thread, args=(db_workq, TEST_DATABASE_SCHEMA))
    tm.create_thread(target=t7_pro_thread, args=(t7_pro_workq, db_workq, labjack_scan_names))

    tm.start_threads()
    while 1:
        time.sleep(1)
