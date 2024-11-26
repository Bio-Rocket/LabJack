import multiprocessing as mp
from br_threading.ThreadManager import ThreadManager as tm
import time

from DatabaseHandler import database_thread
from PlcHandler import plc_thread
from LabjackProcess import t7_pro_thread
from StateMachine import state_thread


if __name__ == "__main__":
    db_workq = mp.Queue()
    plc_workq = mp.Queue()
    t7_pro_workq = mp.Queue()
    state_workq = mp.Queue()

    # Initialize the threads
    tm.create_thread(target=database_thread, args=(db_workq, plc_workq))
    tm.create_thread(target=t7_pro_thread, args=(t7_pro_workq, db_workq))
    tm.create_thread(target=plc_thread, args=(plc_workq, db_workq))
    tm.create_thread(target=state_thread, args=(state_workq, plc_workq))

    tm.start_threads()
    while 1:
        time.sleep(1)
