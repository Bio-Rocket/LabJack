# General imports =================================================================================
import multiprocessing as mp
from pocketbase import Client
from pocketbase.services.realtime_service import MessageData

from br_threading.WorkQCommands import WorkQCmnd, WorkQCmnd_e


# Class Definitions ===============================================================================
class DatabaseHandler():
    def __init__(self, db_thread_workq: mp.Queue):
        """
        Thread to handle the pocketbase database communication.
        The Thread is subscribed to the CommandMessage
        collection to wait for commands created in the front end.
        The handler can also send telemetry data to the database
        to be read by the front end.
        """
        DatabaseHandler.db_thread_workq = db_thread_workq
        DatabaseHandler.client = Client('http://192.168.0.69:8090')
        # DatabaseHandler.client = Client('http://127.0.0.1:8090')

        DatabaseHandler.client.collection('PlcCommands').subscribe(DatabaseHandler._handle_command_callback)

        print("DB - thread started")

    @staticmethod
    def _handle_command_callback(document: MessageData):
        """
        Whenever a new entry is created in the CommandMessage
        collection, this function is called to handle the
        command and forward it to the serial port.

        Args:
            document (MessageData): the change notification from the database.
        """

        print(f"DB - Received {document.record.command} command")
        message = WorkQCmnd(WorkQCmnd_e.COMMAND_FROM_DB, document.record.command)
        DatabaseHandler.db_thread_workq.put(message)

    @staticmethod
    def write_plc_data(plc_data: bytes):
        entry = {}
        entry["plc_data"] = list(plc_data)

        try:
            DatabaseHandler.client.collection("Plc").create(entry)
        except Exception as e:
            print(f"failed to create a plc_data entry {e}")

    @staticmethod
    def write_lj1_data(lj1_data: tuple):
        entry = {}
        entry["lj1_data"] = lj1_data[0]
        entry["device_scan_backlog"] = lj1_data[1]
        entry["ljm_scan_backlog"] = lj1_data[2]

        try:
            DatabaseHandler.client.collection("LabJack1").create(entry)
        except Exception as e:
            print(f"failed to create a lj1_data entry {e}")

# Procedures ======================================================================================
def process_database_command(command: str, plc_workq: mp.Queue) -> None:
    """
    Process the command from the database.

    Args:
        command (str):
            The command from the database.
    """
    if command == "OPEN_SOL":
        plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_SOL, 1)) # Open PLC solenoid 1
    elif command == "CLOSE_SOL":
        plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_SOL, 1)) # Close PLC solenoid 1
    return


def process_workq_message(message: WorkQCmnd, plc_workq: mp.Queue) -> bool:
    """
    Process the message from the workq.

    Args:
        message (WorkQCmnd):
            The message from the workq.
    """
    if message.command == WorkQCmnd_e.KILL_PROCESS:
        print("DB - Received kill command")
        return False
    elif message.command == WorkQCmnd_e.COMMAND_FROM_DB:
        process_database_command(message.data, plc_workq)
    elif message.command == WorkQCmnd_e.PLC_DATA:
        DatabaseHandler.write_plc_data(message.data)
    elif message.command == WorkQCmnd_e.LJ1_DATA:
        DatabaseHandler.write_lj1_data(message.data)

    return True

def database_thread(db_workq: mp.Queue, plc_workq: mp.Queue) -> None:
    """
    The main loop of the database handler. It subscribes to the CommandMessage collection
    """

    DatabaseHandler(db_workq)

    while 1:
        # If there is any workq messages, process them
        if not process_workq_message(db_workq.get(block=True), plc_workq):
            return