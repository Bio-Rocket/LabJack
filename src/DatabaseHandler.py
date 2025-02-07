# General imports =================================================================================
import json
import multiprocessing as mp
from pathlib import Path
import time
from typing import Dict, List, Tuple, Union
from pocketbase import Client
from pocketbase.errors import ClientResponseError
from pocketbase.services.realtime_service import MessageData
from collections import defaultdict
import requests

from LoadcellHandler import LoadCellHandler
from br_threading.WorkQCommands import WorkQCmnd, WorkQCmnd_e
from PlcHandler import PlcData
from LabjackProcess import LAB_JACK_SCAN_RATE, LjData
from dotenv import load_dotenv
import os

PB_URL = 'http://127.0.0.1:8090' # Database Pi IP

EXPECTED_SCHEMA_JSON = os.path.join(Path(__file__).parents[1], "DatabaseSchema.json")

LJ_PACKET_SIZE = LAB_JACK_SCAN_RATE # This makes it so the LJ packet in the DB will contain 1 second of LJ data

# Class Definitions ===============================================================================
class DatabaseHandler():
    def __init__(self, db_thread_workq: mp.Queue, data_base_format_file: str) -> None:
        """
        Thread to handle the pocketbase database communication.
        The Thread is subscribed to the CommandMessage
        collection to wait for commands created in the front end.
        The handler can also send telemetry data to the database
        to be read by the front end.

        Args:
            db_thread_workq (mp.Queue):
                The workq for the database thread.
            data_base_format_file (str):
                The file containing the expected schema for the database.
        """
        DatabaseHandler.db_thread_workq = db_thread_workq
        DatabaseHandler.client = Client(PB_URL)
        DatabaseHandler.token = None

        # Wait for the database to be available
        while not DatabaseHandler.verify_connection():
            print(f"DB - Failed to connect to the database @{PB_URL}, retrying...")
            time.sleep(5)

        # Load environment variables from .env file
        load_dotenv()

        # Get admin credentials from environment variables
        admin_email = os.getenv("ADMIN_EMAIL")
        admin_password = os.getenv("ADMIN_PASS")

        if not admin_email or not admin_password:
            print("DB - Admin credentials not found in environment variables.")
            return

        auth_data = DatabaseHandler.client.collection("_superusers").auth_with_password(admin_email, admin_password)
        DatabaseHandler.token = auth_data.token
        if DatabaseHandler.token is None:
            print("DB - Failed to authenticate as admin.")
            return

        DatabaseHandler.updated_collections(data_base_format_file)

        DatabaseHandler.client.collection('LoadCellCommand').subscribe(DatabaseHandler._handle_load_cell_command_callback)
        DatabaseHandler.client.collection('PlcCommand').subscribe(DatabaseHandler._handle_plc_command_callback)
        DatabaseHandler.client.collection('StateCommand').subscribe(DatabaseHandler._handle_state_command_callback)
        DatabaseHandler.client.collection('HeartbeatMessage').subscribe(DatabaseHandler._handle_heartbeat_callback)

        DatabaseHandler.lj_data_packet: Dict[str, List] = defaultdict(list)
        print("DB - thread started")

    @staticmethod
    def verify_connection() -> bool:
        """
        Verify the connection to the database.

        Returns:
            bool: True if the connection is successful, False otherwise.
        """
        try:
            DatabaseHandler.client.health.check()
            return True
        except ClientResponseError as e:
            return False

    @staticmethod
    def create_collection(collection_name: str, schema: Dict[str, str]) -> None:
        """
        Create a new collection in the database.

        Args:
            collection_name (str): The name of the collection to create.
            schema (Dict[str, str]): The schema of the collection to create.
        """

        try:
            # Create a new collection first
            collection_data = {
                "name": collection_name,
                "type": "base",  # Standard collection type
                "schema": [],  # Will be updated after creation
                "listRule": "",  # Public access
                "viewRule": "",
                "createRule": "",
                "updateRule": "",
                "deleteRule": "",
                "options": {}
            }

            # Create the collection (without schema first)
            created_collection = DatabaseHandler.client.collections.create(collection_data)

            # Build schema fields
            new_schema = []
            for field_name, field_type in schema.items():
                field_data = {
                    "name": field_name,
                    "type": field_type,
                    "required": False,
                    "options": {}
                }

                # Apply type-specific options
                if field_type == "text":
                    field_data["options"] = {"maxSize": 100000}
                elif field_type == "number":
                    field_data["options"] = {"min": None, "max": None}
                new_schema.append(field_data)

            # Include the created and updated timestamps
            new_schema.append({'name': 'updated', 'onCreate': True, 'onUpdate': True, 'type': 'autodate'})
            new_schema.append({'name': 'created', 'onCreate': True, 'onUpdate': False, 'type': 'autodate'})

            # Step 3: Update collection with schema (ensure full schema is provided)
            update_data = {
                "fields": new_schema
            }

            updated_collection = DatabaseHandler.client.collections.update(created_collection.id, update_data)

        except Exception as e:
            print(f"Error creating collection: {e}")


    @staticmethod
    def delete_collection(collection_name: str) -> None:
        """
        Delete a collection from the database.

        Args:
            collection_name (str): The name of the collection to delete.
        """

        # Clear the collection first
        for record in DatabaseHandler.client.collection(collection_name).get_full_list():
            DatabaseHandler.client.collection(collection_name).delete(record.id)

        # Update the collection with the new schema.
        collection_to_update = DatabaseHandler.client.collections.get_one(collection_name)

        # Delete the existing collection
        DatabaseHandler.client.collections.delete(collection_to_update.id)

    @staticmethod
    def updated_collections(format_file: str) -> bool:
        """
        Update the collections in the database to match the expected schema.

        Args:
            format_file (str): The file containing the expected schema for the database.

        Returns:
            bool: True if the collections are updated, False otherwise.
        """
        if not DatabaseHandler.token:
            print("DB - No auth token to update collections")
            return False

        # Get the current collections and their schemas from pocket base
        # Pass the token in the Authorization header
        headers = {"Authorization": f"Bearer {DatabaseHandler.token}"}
        # Assuming client is set to a proper instance, request collections
        collections_url = PB_URL + "/api/collections"
        response = requests.get(collections_url, headers=headers)

        if response.status_code != 200:
            print(f"DB - Could not retrieve collection list, err{response.status_code}: {response.text}")
            return False

        current_schema = {}
        expected_schema = {}

        # Format the current schema for comparison to the expected schema
        collections_data = response.json()
        for collection in collections_data["items"]:
            if collection["system"]: # Skip system collections
                continue

            current_collection_schema = {}

            for field in collection["fields"]:
                if field['system']: # Skip system collections
                    continue
                current_collection_schema[field["name"]] = field["type"]

            current_schema[collection["name"]] = current_collection_schema

        # Load the expected database schema from the json file
        # and format to match current schema format for comparison.
        try:
            with open(format_file, "r") as file:
                expected_data = json.load(file)

                for collection in expected_data["collections"]:
                    collection_name = collection["name"]
                    collection_schema = collection["schema"]

                    expected_collection_schema = {}
                    for field in collection_schema:
                        expected_collection_schema[field["name"]] = field["type"]

                    # Include the created and updated fields for what is expected
                    expected_collection_schema["created"] = "autodate"
                    expected_collection_schema["updated"] = "autodate"

                    expected_schema[collection_name] = expected_collection_schema
        except Exception as e:
            print(f"DB - Could not load expected schema: {e}")
            return False

        # Update and create collections as needed
        for expected_collection in expected_schema:
            # If no collection matches expected collection, create it
            if expected_collection not in current_schema:
                print(f"DB - Creating collection {expected_collection}")
                DatabaseHandler.create_collection(expected_collection, expected_schema[expected_collection])
                continue

            if expected_schema[expected_collection] != current_schema[expected_collection]:
                print(f"DB - Clearing and updating collection {expected_collection}")
                # Drop the collection and recreate it with the new schema.
                DatabaseHandler.delete_collection(expected_collection)
                # Create the new schema by combining the default schema with the expected schema.
                DatabaseHandler.create_collection(expected_collection, expected_schema[expected_collection])
                continue

        # Remove any collections that are not in the expected schema
        for current_collection in current_schema:
            if current_collection not in expected_schema:
                print(f"DB - Removing deprecated collection {current_collection}")
                DatabaseHandler.delete_collection(current_collection)

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
        Whenever a new entry is created in the HeartbeatMessage
        collection, this function is called to handle the
        command and forward it to the state machine to verify
        system state changes are valid

        Args:
            document (MessageData): the change notification from the database.
        """

        if document.record.message == "heartbeat": # This indicates a message from the front end
            DatabaseHandler.db_thread_workq.put(WorkQCmnd(WorkQCmnd_e.FRONTEND_HEARTBEAT, None))

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

        curr_list_len = 0

        # Add the data to the packet
        for key in single_entry:
            if len(DatabaseHandler.lj_data_packet[key]) == 0:
                DatabaseHandler.lj_data_packet[key] = [single_entry[key],]
            else:
                DatabaseHandler.lj_data_packet[key].append(single_entry[key])
            curr_list_len = len(DatabaseHandler.lj_data_packet[key])

        # If the packet is full, write to the database
        if curr_list_len == LJ_PACKET_SIZE:
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
    def write_heartbeat(data: str) -> None:
        """
        Write the heartbeat to the database.

        Args:
            data (str): The heartbeat data to write to the database.
        """
        entry = {}
        entry["message"] = data

        try:
            DatabaseHandler.client.collection("HeartbeatMessage").create(entry)
        except Exception:
            print(f"failed to create a heartbeat")

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

def process_workq_message(message: WorkQCmnd, state_workq: mp.Queue, hb_workq: mp.Queue, lc_handler: LoadCellHandler) -> bool:
    """
    Process the message from the workq.

    Args:
        message (WorkQCmnd):
            The message from the workq.
        state_workq (mp.Queue):
            The state handler workq, used to verify the valve state changes
            along with the system state changes.
        hb_workq (mp.Queue):
            The heartbeat handler workq, used to verify the heartbeat messages.
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
        DatabaseHandler.write_heartbeat(message.data)
    elif message.command == WorkQCmnd_e.FRONTEND_HEARTBEAT:
        hb_workq.put(WorkQCmnd(WorkQCmnd_e.FRONTEND_HEARTBEAT, None))
    elif message.command == WorkQCmnd_e.PLC_DATA:
        DatabaseHandler.write_plc_data(message.data, lc_handler)
    elif message.command == WorkQCmnd_e.LJ_DATA:
        DatabaseHandler.write_lj_data(message.data, lc_handler)

    return True

def database_thread(db_workq: mp.Queue, state_workq: mp.Queue, hb_workq: mp.Queue, data_base_format_file: str = EXPECTED_SCHEMA_JSON) -> None:
    """
    The main loop of the database handler. It subscribes to the CommandMessage collection
    """

    DatabaseHandler(db_workq, data_base_format_file)

    lc_handler = LoadCellHandler()
    for lc in ["LC1", "LC2", "LC3", "LC4", "LC5", "LC6", "LC7"]:
        lc_slope, lc_intercept = DatabaseHandler.get_loadcell_calibration(lc)
        lc_handler.add_load_cell(lc, lc_slope, lc_intercept)

    while 1:
        # If there is any workq messages, process them
        if not process_workq_message(db_workq.get(block=True), state_workq, hb_workq, lc_handler):
            return
