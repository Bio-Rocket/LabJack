import multiprocessing as mp
from os import path
from pathlib import Path
import sys

sys.path.append(path.join(Path(__file__).parents[2].as_posix(), "src/"))

from DatabaseHandler import DatabaseHandler

from PlcHandler import PlcData
from br_threading.WorkQCommands import WorkQCmnd, WorkQCmnd_e

class ValveCycle_DatabaseHandler(DatabaseHandler):

    @staticmethod
    def write_plc_data(plc_data: PlcData) -> None:
        """
        Attempt to write incoming plc data to the database.

        Args:
            plc_data (Tuple[bytes]):
                The plc data, with the first position
                containing the TC data, the second position containing the PT data,
                and the third position containing the valve data.
        """

        if plc_data is None:
            print("DB - plc_data not read correctly")
            return

        pt_data = plc_data.pt_data
        valve_data = plc_data.valve_data

        DatabaseHandler.plc_data_packet["PT1"].append(pt_data[0]*580)
        DatabaseHandler.plc_data_packet["PT2"].append(pt_data[1]*580)
        DatabaseHandler.plc_data_packet["PT3"].append(pt_data[2]*145)

        DatabaseHandler.plc_data_packet["PBV1"].append(valve_data[0])
        DatabaseHandler.plc_data_packet["PBV2"].append(valve_data[1])

        if len(DatabaseHandler.plc_data_packet["PT1"]) == int(1/plc_data.scan_rate):
            try:
                DatabaseHandler.client.collection("Plc").create(DatabaseHandler.plc_data_packet)
            except Exception as e:
                print(f"failed to create a plc_data entry {e}")

            DatabaseHandler.plc_data_packet.clear()

def process_workq_message(message: WorkQCmnd , state_workq: mp.Queue) -> bool:
    """
    Process the message from the workq.

    Args:
        message (WorkQCmnd):
            The message from the workq.
        state_workq (mp.Queue):
            The state workq to put the message into. Handles the valve commands.
    """
    if message.command == WorkQCmnd_e.KILL_PROCESS:
        print("DB - Received kill command")
        return False
    elif message.command == WorkQCmnd_e.DB_GS_COMMAND:
        state_workq.put(WorkQCmnd(WorkQCmnd_e.STATE_HANDLE_VALVE_COMMAND, message.data))
    elif message.command == WorkQCmnd_e.PLC_DATA:
        ValveCycle_DatabaseHandler.write_plc_data(message.data)
    elif message.command == WorkQCmnd_e.DB_STATE_CHANGE:
        DatabaseHandler.write_system_state(message.data)

    return True

def database_thread(db_workq: mp.Queue, state_workq: mp.Queue, data_base_format_file: str) -> None:
    """
    The main loop of the database handler. It subscribes to the CommandMessage collection
    """

    ValveCycle_DatabaseHandler(db_workq, data_base_format_file)

    while 1:
        # If there is any workq messages, process them
        if not process_workq_message(db_workq.get(block=True), state_workq):
            return
