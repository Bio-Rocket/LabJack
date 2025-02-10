import multiprocessing as mp
from os import path
from pathlib import Path
import sys

sys.path.append(path.join(Path(__file__).parents[2].as_posix(), "src/"))

from DatabaseHandler import DatabaseHandler

from PlcHandler import PlcData
from LabjackProcess import GET_SCANS_PER_READ, LjData
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

        entry = {}

        valve_data = list(plc_data.valve_data)

        # The only valves important during this test are outputs
        # 7 and 8 on relay 3, which are linked to the heater and pump 3
        entry["HEATER"] = valve_data[20] # Heater / Relay 3 / Output 7
        entry["PMP3"] = valve_data[21]  # Pump 3 / Relay 3 / Output 8

        try:
            DatabaseHandler.client.collection("Plc").create(entry)
        except Exception as e:
            print(f"failed to create a plc_data entry {e}")


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
                DatabaseHandler.lj_data_packet[key].append(lj_data.pt_data[key].pop(0))
            if len(DatabaseHandler.lj_data_packet[key]) == lj_data.scan_rate:
                try:
                    DatabaseHandler.client.collection("LabJack").create(DatabaseHandler.lj_data_packet)
                except Exception as e:
                    print(f"failed to create a lj_data entry {e}")
                DatabaseHandler.lj_data_packet.clear()


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
    elif message.command == WorkQCmnd_e.LJ_DATA:
        ValveCycle_DatabaseHandler.write_lj_data(message.data)


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
