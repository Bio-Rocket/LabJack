# General imports =================================================================================
import os
import json
import multiprocessing as mp
from typing import Tuple
from pocketbase import Client
from pocketbase.services.realtime_service import MessageData

from WorkQCmnd import WorkQCmnd, WorkQCmnd_e

# Project specific imports ========================================================================
# from src.support.CommonLogger import logger
# from src.ThreadManager import THREAD_MESSAGE_DB_WRITE, THREAD_MESSAGE_KILL, THREAD_MESSAGE_LOAD_CELL_COMMAND, THREAD_MESSAGE_LOAD_CELL_SLOPE, THREAD_MESSAGE_REQUEST_LOAD_CELL_SLOPE, THREAD_MESSAGE_SERIAL_WRITE, THREAD_MESSAGE_STORE_LOAD_CELL_SLOPE, THREAD_MESSAGE_HEARTBEAT, WorkQ_Message
# from src.Utils import Utils as utl

# Class Definitions ===============================================================================
class DatabaseHandler():
    def __init__(self, thread_name: str, thread_workq: mp.Queue):
        """
        Thread to handle the pocketbase database communication.
        The Thread is subscribed to the CommandMessage
        collection to wait for commands created in the front end.
        The handler can also send telemetry data to the database
        to be read by the front end.
        """
        DatabaseHandler.thread_workq = thread_workq
        DatabaseHandler.thread_name = thread_name

        # load_dotenv()
        # db_user = os.getenv('DB_USER')
        # db_password = os.getenv('DB_PASSWORD')

        DatabaseHandler.client = Client('http://127.0.0.1:8090')
        # DatabaseHandler.client.auth_store.clear()
        # DatabaseHandler.client.admins.auth_with_password(db_user, db_password)

        # DatabaseHandler.client.collection('Heartbeat').subscribe(DatabaseHandler._handle_heartbeat_callback)
        # DatabaseHandler.client.collection('CommandMessage').subscribe(DatabaseHandler._handle_command_callback)
        # DatabaseHandler.client.collection('LoadCellCommands').subscribe(DatabaseHandler._handle_load_cell_command_callback)
        #logger.success(f"Successfully started {thread_name} thread")

    @staticmethod
    def _handle_heartbeat_callback(document: MessageData):
        """
        Whenever a new entry is created in the Heartbeat
        collection, this function is called to handle the
        command and forward it to the HeartbeatHandler.

        Args:
            document (MessageData): the change notification from the database.
        """
        DatabaseHandler.thread_workq.put(
            WorkQCmnd(WorkQCmnd_e.HEART_BEAT, None)
        )

    @staticmethod
    def _handle_command_callback(document: MessageData):
        """
        Whenever a new entry is created in the CommandMessage
        collection, this function is called to handle the
        command and forward it to the serial port.

        Args:
            document (MessageData): the change notification from the database.
        """

        logger.info("Received new command from the database")
        logger.debug(f"Record command: {document.record.command}")
        DatabaseHandler.send_message_workq.put(
            WorkQ_Message(
                DatabaseHandler.thread_name,
                'all_serial',
                THREAD_MESSAGE_SERIAL_WRITE,
                (document.record.command,
                 document.record.target,
                 document.record.command_param,
                 document.record.source_sequence_num
                )
            )
        )

    @staticmethod
    def _handle_load_cell_command_callback(document: MessageData):
        """
        Whenever a new entry is created in the LoadCellCommands
        collection, this function is called to handle the command
        and forward it to the load cell handler.

        Args:
            document (MessageData):
                the change notification from the database.
        """
        logger.info("Received new load cell command from the database")
        logger.debug(f"Record command: {document.record.command}")
        DatabaseHandler.send_message_workq.put(
            WorkQ_Message(
                DatabaseHandler.thread_name,
                'loadcell',
                THREAD_MESSAGE_LOAD_CELL_COMMAND,
                (document.record.target, document.record.command, document.record.weight)
            )
        )

    @staticmethod
    def send_telemetry_message_to_database(json_data: str):
        """
        Send a preserialized JSON message to the database.

        Note: The third key in the JSON data is assumed to be the table name
        """
        # Extract the table name from the JSON data
        json_data = json.loads(json_data)
        if len(list(json_data.keys())) < 3:
            logger.warning(f"Received, poorly formed json: {json_data}")
            return

        table_name = list(json_data.keys())[2]

        logger.info(f"Adding an entry to the {table_name} table")
        logger.info(f"Entry: {json_data[table_name]}")

        # Push the JSON data to PocketBase using the correct schema
        try:
            DatabaseHandler.client.collection(table_name).create(json_data[table_name])
        except Exception:
            logger.error(f"Failed to create entry in {table_name}: {json_data}")

    @staticmethod
    def send_load_cell_cali_to_database(thread_message: Tuple[str, str]):
        """
        Send a preserialized JSON message to the database.
        """

        load_cell_name = thread_message[0]
        json_data = thread_message[1]

        logger.info(f"Updating an entry to the LoadCellCalibrationCurves table")
        logger.info(f"Entry: {json_data}")

        # Push the JSON data to PocketBase using the correct schema
        try:
            record = DatabaseHandler.client.collection('LoadCellCalibrationCurves').get_first_list_item(f'name="{load_cell_name}"')
            entry_exists = True
        except Exception:
            entry_exists = False
            logger.debug(f"No existing slope for {load_cell_name}, creating new entry")

        try:
            if entry_exists:
                DatabaseHandler.client.collection("LoadCellCalibrationCurves").update(record.id, json.loads(json_data))
            else:
                DatabaseHandler.client.collection("LoadCellCalibrationCurves").create(json.loads(json_data))
        except Exception as e:
            if entry_exists:
                logger.error(f"Failed to update entry in LoadCellCalibrationCurves: {json_data}\n{e}")
            else:
                logger.error(f"Failed to create entry in LoadCellCalibrationCurves: {json_data}\n{e}")

    @staticmethod
    def get_load_cell_cali_from_database(load_cell_name: str):
        """
        Get the load cell calibration curve from the database.
        """
        try:
            record = DatabaseHandler.client.collection('LoadCellCalibrationCurves').get_first_list_item(f'name="{load_cell_name}"')
            DatabaseHandler.send_message_workq.put(
                WorkQ_Message(
                    DatabaseHandler.thread_name,
                    'loadcell',
                    THREAD_MESSAGE_LOAD_CELL_SLOPE,
                    (load_cell_name, record.slope, record.intercept)
                )
            )
        except Exception as e:
            logger.error(f"Failed to get {load_cell_name} calibration curve from the database: {e}")


    @staticmethod
    def write_to_pressure_transducer_table(pressure_transducer_voltage_arr: list):
        """
        Send the pressure transducer voltage list to the database.
        """
        voltage_dict = {f"PT{i+1}": voltage for i, voltage in enumerate(pressure_transducer_voltage_arr)}

        # Push the list to PocketBase using the correct schema
        try:
            DatabaseHandler.client.collection("LabjackPressureTransducers").create(voltage_dict)
        except Exception:
            print(f"Failed to create entry in LabjackPressureTransducers: {voltage_dict}")
            #logger.error(f"Failed to create entry in {table_name}: {json_data}")

    @staticmethod
    def write_to_load_cell_table(load_cell_voltage_arr: list):
        """
        Send the loadcell voltage list to the database.
        """
        #voltage_dict = {f"LC{i+1}": voltage for i, voltage in enumerate(load_cell_voltage_arr)}
        voltage_dict = {"LC1" : 123.4, "LC2" : 123.4, "LC3" : 123.4, "LC4" : 123.4}

        # Push the list to PocketBase using the correct schema
        try:
            DatabaseHandler.client.collection("LabjackLoadCells").create(voltage_dict)
        except Exception:
            print(f"Failed to create entry in LabjackLoadCells: {voltage_dict}")
            #logger.error(f"Failed to create entry in {table_name}: {json_data}")

    @staticmethod
    def write_to_backlog_table(backlog_arr: list):
        """
        Send the backlog list to the database.
        """
        backlog_dict = {f"deviceScanBacklog": backlog_arr[0], "ljmScanBacklog": backlog_arr[1]}

        # Push the list to PocketBase using the correct schema
        try:
            DatabaseHandler.client.collection("LabjackBackLog").create(backlog_dict)
        except Exception:
            print(f"Failed to create entry in LabjackBackLog: {backlog_dict}")
            #logger.error(f"Failed to create entry in {table_name}: {json_data}")


# Procedures ======================================================================================
def database_thread(thread_name: str, db_workq) -> None:
    """
    The main loop of the database handler. It subscribes to the CommandMessage collection
    """

    DatabaseHandler(thread_name, db_workq)

    while 1:
        # If there is any workq messages, process them
        if not process_workq_message(db_workq.get(block=True)):
            return

def process_workq_message(message) -> bool:
    """
    Process the message from the workq.

    Args:
        message (WorkQ_Message):
            The message from the workq.
    """
    return True