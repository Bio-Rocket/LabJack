import multiprocessing as mp
import threading
import time

from br_threading.WorkQCommands import WorkQCmnd, WorkQCmnd_e

# Project specific imports ========================================================================
BACKEND_HEARTBEAT_DELAY = 30
FRONTEND_DISCONNECT_TIMEOUT = 20 * 60 # 20 minutes

def send_hb_to_db(db_workq: mp.Queue):
    """
    Notify DB backend is Live
    """
    while True:
        db_workq.put(WorkQCmnd(WorkQCmnd_e.DB_HEARTBEAT, "BACKEND"))
        time.sleep(BACKEND_HEARTBEAT_DELAY)

def wait_for_frontend(frontend_notification: threading.Event, state_workq: mp.Queue):
    """
    Wait for the frontend to send a heartbeat.
    """
    while True:
        frontend_notification.wait(timeout=FRONTEND_DISCONNECT_TIMEOUT)
        if not frontend_notification.is_set():
            # The system will continue to run even if no frontend heartbeat is received
            # until it is either stopped through SSH or the frontend connects
            print("HB - No Heartbeat from frontend: GOING TO ABORT")
            state_workq.put(WorkQCmnd(WorkQCmnd_e.STATE_TRANSITION, "GOTO_ABORT"))
        frontend_notification.clear()

def process_workq_message(message: WorkQCmnd, frontend_notification: threading.Event) -> bool:
    """
    Process the message from the workq.

    Args:
        message (WorkQCmnd_e):
            The message from the workq.
        frontend_notification (threading.Event):
            The event to notify the backend timeout thread that
            the frontend is still alive.
    """
    if message.command == WorkQCmnd_e.KILL_PROCESS:
        return False
    elif message.command == WorkQCmnd_e.FRONTEND_HEARTBEAT:
        print("HB - Received heartbeat from frontend")
        frontend_notification.set()
    return True

def heartbeat_thread(hb_workq: mp.Queue, db_workq: mp.Queue, state_workq: mp.Queue):
    """
    The main loop of the heartbeat handler.

    This function will continuously send a HB to the DB to demonstrate a connection.
    """
    # Start the background task in a separate thread
    notify_frontend_thread = threading.Thread(target=send_hb_to_db, args=(db_workq,))
    notify_frontend_thread.daemon = True
    notify_frontend_thread.start()

    frontend_notification = threading.Event()
    wait_for_frontend_thread = threading.Thread(target=wait_for_frontend, args=(frontend_notification, state_workq))
    wait_for_frontend_thread.daemon = True
    wait_for_frontend_thread.start()

    print("HB - thread started")

    while True:
        # If there is any workq messages, process them
        if not process_workq_message(hb_workq.get(block=True), frontend_notification):
            return