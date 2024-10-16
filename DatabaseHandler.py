# General imports =================================================================================
import json
import multiprocessing as mp
from typing import Tuple
from pocketbase import Client
from pocketbase.services.realtime_service import MessageData

from br_threading.WorkQCommands import WorkQCmnd, WorkQCmnd_e

LOADCELL_COMMANDS = ["TARE", "CANCEL", "CALIBRATE", "FINISH"]

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
        DatabaseHandler.client = Client('http://192.168.0.69:8090') # Database Pi IP

        DatabaseHandler.client.collection('PlcCommands').subscribe(DatabaseHandler._handle_plc_command_callback)
        DatabaseHandler.client.collection('LabJack1Commands').subscribe(DatabaseHandler._handle_lj1_command_callback)
        DatabaseHandler.client.collection('LabJack2Commands').subscribe(DatabaseHandler._handle_lj2_command_callback)
        DatabaseHandler.client.collection('Heartbeat').subscribe(DatabaseHandler._handle_heartbeat_callback)

        print("DB - thread started")

    @staticmethod
    def _handle_plc_command_callback(document: MessageData):
        """
        Whenever a new entry is created in the PlcCommands
        collection, this function is called to handle the
        command and forward it to the serial port.

        Args:
            document (MessageData): the change notification from the database.
        """
        DatabaseHandler.db_thread_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_DB_COMMAND, (document.record.command, document.record.loadcell, document.record.value)))

    @staticmethod
    def _handle_lj1_command_callback(document: MessageData):
        """
        Whenever a new entry is created in the LabJack1Commands
        collection, this function is called to handle the
        command and forward it to the LabJack1.

        Args:
            document (MessageData): the change notification from the database.
        """
        DatabaseHandler.db_thread_workq.put(WorkQCmnd(WorkQCmnd_e.LJ1_DB_COMMAND, (document.record.command, document.record.value)))

    @staticmethod
    def _handle_lj2_command_callback(document: MessageData):
        """
        Whenever a new entry is created in the LabJack2Commands
        collection, this function is called to handle the
        command and forward it to the LabJack2.

        Args:
            document (MessageData): the change notification from the database.
        """
        DatabaseHandler.db_thread_workq.put(WorkQCmnd(WorkQCmnd_e.LJ2_DB_COMMAND, (document.record.command, document.record.value)))

    @staticmethod
    def _handle_heartbeat_callback(document: MessageData):
        """
        Whenever a new entry is created in the Heartbeat
        collection, this function is called to handle the
        command and forward it to the serial port.

        Args:
            document (MessageData): the change notification from the database.
        """
        DatabaseHandler.db_thread_workq.put(WorkQCmnd(WorkQCmnd_e.DB_HEART_BEAT, None))

    @staticmethod
    def write_plc_data(plc_data: Tuple[bytes]):

        if len(plc_data) != 3:
            print("plc_data tuple is not of length 3")
            return

        entry = {}

        tc_data = list(plc_data[0])
        entry["TC1"] = tc_data[0]
        entry["TC2"] = tc_data[1]
        entry["TC3"] = tc_data[2]
        entry["TC4"] = tc_data[3]
        entry["TC5"] = tc_data[4]
        entry["TC6"] = tc_data[5]
        entry["TC7"] = tc_data[6]
        entry["TC8"] = tc_data[7]
        entry["TC9"] = tc_data[8]

        entry["LC1"] = tc_data[9]
        entry["LC2"] = tc_data[10]

        pt_data = list(plc_data[1])
        entry["PT1_voltage"] = pt_data[0]
        entry["PT2_voltage"] = pt_data[1]
        entry["PT3_voltage"] = pt_data[2]
        entry["PT4_voltage"] = pt_data[3]
        entry["PT5_voltage"] = pt_data[4]
        entry["PT6_voltage"] = pt_data[5]
        entry["PT15_voltage"] = pt_data[6]
        entry["PT16_voltage"] = pt_data[7]

        valve_data = list(plc_data[2])
        entry["PBV1_state"] = valve_data[0]
        entry["PBV2_state"] = valve_data[1]
        entry["PBV3_state"] = valve_data[2]
        entry["PBV4_state"] = valve_data[3]
        entry["PBV5_state"] = valve_data[4]
        entry["PBV6_state"] = valve_data[5]
        entry["PBV7_state"] = valve_data[6]
        entry["PBV8_state"] = valve_data[7]

        entry["PMP1_state"] = valve_data[8]
        entry["PMP2_state"] = valve_data[9]
        entry["PMP3_state"] = valve_data[10]

        entry["IGN1_state"] = valve_data[11]
        entry["IGN2_state"] = valve_data[12]

        entry["Heater_state"] = valve_data[13]

        try:
            DatabaseHandler.client.collection("PLC").create(entry)
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
    if command == "PBV1_OPEN":
        plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 1))
    elif command == "PBV2_OPEN":
        plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 2))
    elif command == "PBV3_OPEN":
        plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 3))
    elif command == "PBV4_OPEN":
        plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 4))
    elif command == "PBV5_OPEN":
        plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 5))
    elif command == "PBV6_OPEN":
        plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 6))
    elif command == "PBV7_OPEN":
        plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 7))
    elif command == "PBV8_OPEN":
        plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 8))
    elif command == "PMP1_ON":
        plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_PUMP_ON, 1))
    elif command == "PMP2_ON":
        plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_PUMP_ON, 2))
    elif command == "PMP3_ON":
        plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_PUMP_ON, 3))
    elif command == "IGN1_ON":
        plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_IGN_ON, 2))
    elif command == "IGN2_ON":
        plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_IGN_ON, 1))
    elif command == "HEATER_ON":
        plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_HEATER_ON, None))

    elif command == "PBV1_CLOSE":
        plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 1))
    elif command == "PBV2_CLOSE":
        plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 2))
    elif command == "PBV3_CLOSE":
        plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 3))
    elif command == "PBV4_CLOSE":
        plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 4))
    elif command == "PBV5_CLOSE":
        plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 5))
    elif command == "PBV6_CLOSE":
        plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 6))
    elif command == "PBV7_CLOSE":
        plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 7))
    elif command == "PBV8_CLOSE":
        plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 8))
    elif command == "PMP1_OFF":
        plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_PUMP_OFF, 1))
    elif command == "PMP2_OFF":
        plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_PUMP_OFF, 2))
    elif command == "PMP3_OFF":
        plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_PUMP_OFF, 3))
    elif command == "IGN1_OFF":
        plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_IGN_OFF, 2))
    elif command == "IGN2_OFF":
        plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_IGN_OFF, 1))
    elif command == "HEATER_OFF":
        plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_HEATER_OFF, None))

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
    elif message.command == WorkQCmnd_e.PLC_DB_COMMAND:
        if message.data[0] in LOADCELL_COMMANDS:
            print("LOAD_CELL_COMMAND NOT YET SUPPORTED") # TODO
        else:
            process_database_command(message.data, plc_workq)
    elif message.command == WorkQCmnd_e.LJ1_DB_COMMAND:
        pass # TODO
    elif message.command == WorkQCmnd_e.LJ2_DB_COMMAND:
        pass # TODO
    elif message.command == WorkQCmnd_e.DB_HEART_BEAT:
        pass # TODO
    elif message.command == WorkQCmnd_e.PLC_DATA:
        DatabaseHandler.write_plc_data(message.data)
    elif message.command == WorkQCmnd_e.LJ1_DATA:
        DatabaseHandler.write_lj1_data(message.data)

    return True

def database_thread(db_workq: mp.Queue, plc_workq: mp.Queue) -> None: #TODO: will need workq for LabJack
    """
    The main loop of the database handler. It subscribes to the CommandMessage collection
    """

    DatabaseHandler(db_workq)

    while 1:
        # If there is any workq messages, process them
        if not process_workq_message(db_workq.get(block=True), plc_workq):
            return