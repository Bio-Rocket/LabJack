import multiprocessing as mp
from os import path
from pathlib import Path
import sys

sys.path.append(path.join(Path(__file__).parents[2].as_posix(), "src/"))

from DatabaseHandler import DatabaseHandler
from LabjackProcess import GET_SCANS_PER_READ, LjData
from br_threading.WorkQCommands import WorkQCmnd, WorkQCmnd_e

PRESSURE_MODIFIER = lambda x: 571.77 * x - 362.5
PU_VOLTAGE_MODIFIER = 870

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
        """

        for i in range(GET_SCANS_PER_READ(lj_data.scan_rate)):
            for key in lj_data.pt_data:
                if key == "PT1":
                    pt1_raw = lj_data.pt_data[key].pop(0)
                    DatabaseHandler.lj_data_packet["raw_voltage_PT1"].append(pt1_raw)
                    DatabaseHandler.lj_data_packet[key].append(PRESSURE_MODIFIER(pt1_raw))
                else:
                    DatabaseHandler.lj_data_packet[key].append(lj_data.pt_data[key].pop(0) * PU_VOLTAGE_MODIFIER)
            if len(DatabaseHandler.lj_data_packet[key]) == lj_data.scan_rate:
                try:
                    DatabaseHandler.client.collection("LabJack").create(DatabaseHandler.lj_data_packet)
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
