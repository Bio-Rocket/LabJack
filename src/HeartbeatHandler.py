import multiprocessing as mp
import threading
import time

from br_threading.WorkQCommands import WorkQCmnd, WorkQCmnd_e

# Project specific imports ========================================================================
BACKEND_HEARTBEAT_DELAY = 30

def process_workq_message(message: WorkQCmnd) -> bool:
    """
    Process the message from the workq.

    Args:
        message (WorkQCmnd_e):
            The message from the workq.
    """
    if message.command == WorkQCmnd_e.KILL_PROCESS:
        return False
    return True

def send_hb_to_db(db_workq: mp.Queue):
    """
    Notify DB backend is Live
    """
    while True:
        db_workq.put(WorkQCmnd(WorkQCmnd_e.DB_HEARTBEAT, "BACKEND"))
        time.sleep(BACKEND_HEARTBEAT_DELAY)

def heartbeat_thread(hb_workq: mp.Queue, db_workq: mp.Queue):
    """
    The main loop of the heartbeat handler.

    This function will continuously send a HB to the DB to demonstrate a connection.
    """
    # Start the background task in a separate thread
    background_thread = threading.Thread(target=send_hb_to_db, args=(db_workq,))
    background_thread.daemon = True
    background_thread.start()
    print("HB - thread started")

    while True:
        # If there is any workq messages, process them
        if not process_workq_message(hb_workq.get(block=True)):
            return