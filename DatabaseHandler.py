# General imports =================================================================================
import multiprocessing as mp
from typing import Dict, List, Tuple
from pocketbase import Client
from pocketbase.services.realtime_service import MessageData

from LoadcellHandler import LoadCellHandler
from br_threading.WorkQCommands import WorkQCmnd, WorkQCmnd_e
from PlcHandler import PlcData
from LabjackProcess import LAB_JACK_SCAN_RATE, LjData

LJ_PACKET_SIZE = LAB_JACK_SCAN_RATE # This makes it so the LJ packet in the DB will contain 1 second of LJ data

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
        # DatabaseHandler.client = Client('http://192.168.0.69:8090') # Database Pi IP
        DatabaseHandler.client = Client('http://127.0.0.1:8090') # Database Pi IP

        DatabaseHandler.client.collection('LoadCellCommands').subscribe(DatabaseHandler._handle_load_cell_command_callback)
        DatabaseHandler.client.collection('PlcCommands').subscribe(DatabaseHandler._handle_plc_command_callback)
        DatabaseHandler.client.collection('StateCommands').subscribe(DatabaseHandler._handle_state_command_callback)
        DatabaseHandler.client.collection('Heartbeat').subscribe(DatabaseHandler._handle_heartbeat_callback)

        DatabaseHandler.lj_data_packet: Dict[str, List] = []
        print("DB - thread started")

    @staticmethod
    def _handle_plc_command_callback(document: MessageData):
        """
        Whenever a new entry is created in the PlcCommands
        collection, this function is called to handle the
        command and forward it to the state machine to verify
        valve changes are valid.

        Args:
            document (MessageData): the change notification from the database.
        """
        print(f"DB - PLC Command: {document.record.command}")
        DatabaseHandler.db_thread_workq.put(WorkQCmnd(WorkQCmnd_e.DB_PLC_COMMAND, document.record.command))

    @staticmethod
    def _handle_load_cell_command_callback(document: MessageData):
        """
        Whenever a new entry is created in the LoadCellCommands
        collection, this function is called to handle the
        command and forward it to the load cell handler.

        Args:
            document (MessageData): the change notification from the database.
        """
        DatabaseHandler.db_thread_workq.put(WorkQCmnd(WorkQCmnd_e.DB_LC_COMMAND, (document.record.command, document.record.loadcell, document.record.value)))

    @staticmethod
    def _handle_state_command_callback(document: MessageData):
        """
        Whenever a new entry is created in the StateCommands
        collection, this function is called to handle the
        command and forward it to the state machine to verify
        system state changes are valid

        Args:
            document (MessageData): the change notification from the database.
        """
        DatabaseHandler.db_thread_workq.put(WorkQCmnd(WorkQCmnd_e.DB_STATE_COMMAND, (document.record.command)))

    @staticmethod
    def _handle_heartbeat_callback(document: MessageData):
        """
        Whenever a new entry is created in the Heartbeat
        collection, this function is called to handle the
        command and forward it to the serial port.

        Args:
            document (MessageData): the change notification from the database.
        """
        DatabaseHandler.db_thread_workq.put(WorkQCmnd(WorkQCmnd_e.DB_HEARTBEAT, None))

    @staticmethod
    def write_plc_data(plc_data: PlcData, lc_handler: LoadCellHandler) -> None:
        """
        Attempt to write incoming plc data to the database.

        Args:
            plc_data (Tuple[bytes]):
                The plc data, with the first position
                containing the TC data, the second position containing the PT data,
                and the third position containing the valve data.
            lc_handler (LoadCellHandler):
                The load cell handler to handle the load cell mass conversions.
        """

        if plc_data is None:
            print("DB - plc_data not read correctly")
            return

        entry = {}

        tc_data = list(plc_data.tc_data)
        entry["TC1"] = tc_data[0]
        entry["TC2"] = tc_data[1]
        entry["TC3"] = tc_data[2]
        entry["TC4"] = tc_data[3]
        entry["TC5"] = tc_data[4]
        entry["TC6"] = tc_data[5]
        entry["TC7"] = tc_data[6]
        entry["TC8"] = tc_data[7]
        entry["TC9"] = tc_data[8]

        lc_data = list(plc_data.lc_data)
        entry["LC1"] = lc_handler.consume_incoming_voltage("LC1", lc_data[0])
        entry["LC2"] = lc_handler.consume_incoming_voltage("LC2", lc_data[1])
        entry["LC7"] = lc_handler.consume_incoming_voltage("LC7", lc_data[2])

        pt_data = list(plc_data.pt_data)
        entry["PT1"] = pt_data[0]
        entry["PT2"] = pt_data[1]
        entry["PT3"] = pt_data[2]
        entry["PT4"] = pt_data[3]
        entry["PT5"] = pt_data[4]
        entry["PT13"] = pt_data[5]
        entry["PT14"] = pt_data[6]

        valve_data = list(plc_data.valve_data)
        entry["PBV1"] = valve_data[0]
        entry["PBV2"] = valve_data[1]
        entry["PBV3"] = valve_data[2]
        entry["PBV4"] = valve_data[3]
        entry["PBV5"] = valve_data[4]
        entry["PBV6"] = valve_data[5]
        entry["PBV7"] = valve_data[6]
        entry["PBV8"] = valve_data[7]
        entry["PBV9"] = valve_data[8]
        entry["PBV10"] = valve_data[9]
        entry["PBV11"] = valve_data[10]

        entry["SOL1"] = valve_data[11]
        entry["SOL2"] = valve_data[12]
        entry["SOL3"] = valve_data[13]
        entry["SOL4"] = valve_data[14]
        entry["SOL5"] = valve_data[15]
        entry["SOL6"] = valve_data[16]
        entry["SOL7"] = valve_data[17]
        entry["SOL8"] = valve_data[18]
        entry["SOL9"] = valve_data[19]

        entry["HEATER"] = valve_data[20]

        entry["PMP3"] = valve_data[21] #TODO: Currently not used Pump (PMP3)

        entry["IGN1"] = valve_data[22]
        entry["IGN2"] = valve_data[23]

        try:
            DatabaseHandler.client.collection("PLC").create(entry)
        except Exception as e:
            print(f"failed to create a plc_data entry {e}")


    @staticmethod
    def write_lj_data(lj_data: LjData, lc_handler: LoadCellHandler) -> None:
        """
        Attempt to write incoming labjack data to the database.

        Batch Write Feature:
        If there is a LJ_PACKET_SIZE specified, the DB handler will
        collect that many pieces of data and write to the DB once the
        full package is complete, this allows for faster DB writes.

        Args:
            lj_data (tuple): The labjack data, with the first position
                containing the list of data
            lc_handler (LoadCellHandler):
                The load cell handler to handle the load cell mass conversions.
        """

        single_entry = {}

        # Convert the load cell voltages to masses
        single_entry["LC3"] = lc_handler.consume_incoming_voltage("LC3", lj_data.lc_data[0])
        single_entry["LC4"] = lc_handler.consume_incoming_voltage("LC4", lj_data.lc_data[1])
        single_entry["LC5"] = lc_handler.consume_incoming_voltage("LC5", lj_data.lc_data[2])
        single_entry["LC6"] = lc_handler.consume_incoming_voltage("LC6", lj_data.lc_data[3])

        single_entry["PT6"] = lj_data.pt_data[0]
        single_entry["PT7"] = lj_data.pt_data[1]
        single_entry["PT8"] = lj_data.pt_data[2]
        single_entry["PT9"] = lj_data.pt_data[3]
        single_entry["PT10"] = lj_data.pt_data[4]
        single_entry["PT11"] = lj_data.pt_data[5]
        single_entry["PT12"] = lj_data.pt_data[6]

        # Add the data to the packet
        for key in single_entry:
            if len(DatabaseHandler.lj_data_packet[key]) == 0:
                DatabaseHandler.lj_data_packet[key] = list().append(single_entry[key])
            else:
                DatabaseHandler.lj_data_packet[key].append(single_entry[key])

        # If the packet is full, write to the database
        if len(DatabaseHandler.lj_data_packet.values()[0]) == LJ_PACKET_SIZE:
            entry = {}
            entry["LC3"] = DatabaseHandler.lj_data_packet["LC3"]
            entry["LC4"] = DatabaseHandler.lj_data_packet["LC4"]
            entry["LC5"] = DatabaseHandler.lj_data_packet["LC5"]
            entry["LC6"] = DatabaseHandler.lj_data_packet["LC6"]

            entry["PT6"] = DatabaseHandler.lj_data_packet["PT6"]
            entry["PT7"] = DatabaseHandler.lj_data_packet["PT7"]
            entry["PT8"] = DatabaseHandler.lj_data_packet["PT8"]
            entry["PT9"] = DatabaseHandler.lj_data_packet["PT9"]
            entry["PT10"] = DatabaseHandler.lj_data_packet["PT10"]
            entry["PT11"] = DatabaseHandler.lj_data_packet["PT11"]
            entry["PT12"] = DatabaseHandler.lj_data_packet["PT12"]

            try:
                DatabaseHandler.client.collection("LabJack").create(entry)
            except Exception as e:
                print(f"failed to create a lj_data entry {e}")
            DatabaseHandler.lj_data_packet.clear()

    @staticmethod
    def write_lc_calibration(loadcell: str, slope: float, intercept: float) -> None:
        """
        Write the load cell calibration to the database.

        Args:
            data (Tuple[str, LoadCellHandler]):
                The load cell calibration data.
        """
        entry = {}
        entry["loadcell"] = loadcell
        entry["slope"] = slope
        entry["intercept"] = intercept

        try:
            DatabaseHandler.client.collection("LoadCellCalibration").create(entry)
        except Exception as e:
            print(f"failed to create a load cell calibration")

    @staticmethod
    def write_system_state(state: str) -> None:
        """
        Write the system state to the database.

        Args:
            state (str): The system state to write to the database.
        """
        entry = {}
        entry["system_state"] = state

        try:
            DatabaseHandler.client.collection("SystemState").create(entry)
        except Exception:
            print(f"failed to create a system state")

    @staticmethod
    def get_loadcell_calibration(loadcell: str) -> Tuple[float, float]:
        """
        Get the load cell calibration from the database.

        Args:
            loadcell (str): The load cell to get the calibration for.

        Returns:
            Tuple[float, float]: The slope and intercept of the load cell calibration.
        """
        try:
            calibration = DatabaseHandler.client.collection("LoadCellCalibration").find_one({"loadcell": loadcell})
            return calibration["slope"], calibration["intercept"]
        except Exception as e:
            print(f"No calibration for {loadcell} -  {e}")
            return 1, 0

# Procedures ======================================================================================

def handle_lc_command(data: Tuple[str, str, float], lc_handler: LoadCellHandler) -> None:
    """
    Handle the load cell command from the database.

    Args:
        data (Tuple[str, str, float]):
            command, load cell, value.
        lc_handler (LoadCellHandler):
            The load cell handler to handle the load cell commands.
    """
    command, loadcell, value = data

    if command == "TARE":
        lc_handler.tare_load_cell(loadcell)
    elif command == "CANCEL":
        lc_handler.cancel_calibration(loadcell)
    elif command == "CALIBRATE":
        lc_handler.add_calibration_mass(loadcell, value)
    elif command == "FINISH":
        lc_handler.add_calibration_mass(loadcell, value, final_mass=True)
        slope, intercept = lc_handler.get_calibration(loadcell)
        DatabaseHandler.write_lc_calibration(loadcell, slope, intercept)

def process_workq_message(message: WorkQCmnd, state_workq: mp.Queue, lc_handler: LoadCellHandler) -> bool:
    """
    Process the message from the workq.

    Args:
        message (WorkQCmnd):
            The message from the workq.
        state_workq (mp.Queue):
            The state handler workq, used to verify the valve state changes
            along with the system state changes.
        lc_handler (LoadCellHandler):
            The load cell handler to handle the load cell commands.
    """
    if message.command == WorkQCmnd_e.KILL_PROCESS:
        print("DB - Received kill command")
        return False
    elif message.command == WorkQCmnd_e.DB_PLC_COMMAND:
        state_workq.put(WorkQCmnd(WorkQCmnd_e.STATE_HANDLE_VALVE_COMMAND, message.data))
    elif message.command == WorkQCmnd_e.DB_LC_COMMAND:
        handle_lc_command(message.data, lc_handler)
    elif message.command == WorkQCmnd_e.DB_STATE_COMMAND:
        state_workq.put(WorkQCmnd(WorkQCmnd_e.STATE_TRANSITION, message.data))
    elif message.command == WorkQCmnd_e.DB_STATE_CHANGE:
        DatabaseHandler.write_system_state(message.data)
    elif message.command == WorkQCmnd_e.DB_HEARTBEAT:
        pass # TODO
    elif message.command == WorkQCmnd_e.PLC_DATA:
        DatabaseHandler.write_plc_data(message.data, lc_handler)
    elif message.command == WorkQCmnd_e.LJ_DATA:
        DatabaseHandler.write_lj_data(message.data, lc_handler)

    return True

def database_thread(db_workq: mp.Queue, state_workq: mp.Queue) -> None:
    """
    The main loop of the database handler. It subscribes to the CommandMessage collection
    """

    DatabaseHandler(db_workq)

    lc_handler = LoadCellHandler()
    for lc in ["LC1", "LC2", "LC3", "LC4", "LC5", "LC6", "LC7"]:
        lc_slope, lc_intercept = DatabaseHandler.get_loadcell_calibration(lc)
        lc_handler.add_load_cell(lc, lc_slope, lc_intercept)

    while 1:
        # If there is any workq messages, process them
        if not process_workq_message(db_workq.get(block=True), state_workq, lc_handler):
            return