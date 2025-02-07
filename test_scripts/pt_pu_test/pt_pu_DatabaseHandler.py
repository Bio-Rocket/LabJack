import multiprocessing as mp
from os import path
from pathlib import Path
import sys

sys.path.append(path.join(Path(__file__).parents[2].as_posix(), "src/"))

from DatabaseHandler import LJ_PACKET_SIZE, DatabaseHandler
from LabjackProcess import LjData
from br_threading.WorkQCommands import WorkQCmnd, WorkQCmnd_e

VOLTAGE_MODIFIER = 2

class PtPu_DatabaseHandler(DatabaseHandler):

    @staticmethod
    def write_lj_data(lj_data: LjData) -> None:
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
        single_entry["PT1"] = lj_data.pt_data[0]
        single_entry["raw_voltage"] = lj_data.pt_data[1]
        single_entry["corrected_voltage"] = lj_data.pt_data[1] * VOLTAGE_MODIFIER

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
            entry["PT1"] = DatabaseHandler.lj_data_packet["PT1"]
            entry["raw_voltage"] = DatabaseHandler.lj_data_packet["raw_voltage"]
            entry["corrected_voltage"] = DatabaseHandler.lj_data_packet["corrected_voltage"]

            try:
                DatabaseHandler.client.collection("LabJack").create(entry)
            except Exception as e:
                print(f"failed to create a lj_data entry {e}")
            DatabaseHandler.lj_data_packet.clear()


def process_workq_message(message: WorkQCmnd) -> bool:
    """
    Process the message from the workq.

    Args:
        message (WorkQCmnd):
            The message from the workq.
    """
    if message.command == WorkQCmnd_e.KILL_PROCESS:
        print("DB - Received kill command")
        return False
    elif message.command == WorkQCmnd_e.LJ_DATA:
        PtPu_DatabaseHandler.write_lj_data(message.data)

    return True

def database_thread(db_workq: mp.Queue, data_base_format_file: str) -> None:
    """
    The main loop of the database handler. It subscribes to the CommandMessage collection
    """

    PtPu_DatabaseHandler(db_workq, data_base_format_file)

    while 1:
        # If there is any workq messages, process them
        if not process_workq_message(db_workq.get(block=True)):
            return
