# General imports =================================================================================
import multiprocessing as mp
from socket import socket, AF_INET, SOCK_STREAM
from typing import Tuple
from br_threading.WorkQCommands import WorkQCmnd, WorkQCmnd_e
from br_threading.TimerThread import TimerThread
from dataclasses import dataclass

# Constants ========================================================================================
PLC_IP = "192.168.0.70"
PLC_PORT = 69

REQUEST_DELAY = (1.0/50.0) # in seconds

# PLC Commands and Offsets
PLC_REQUEST = 1

PLC_PBV_OFFSET = 9
SOL_OFFSET = 20

PLC_HEATER_CMND = 30
PUMP3_CMND = 31

PLC_IGN_OFFSET = 31

# PLC data sizes
PLC_TC_DATA_SIZE = 9 * 2 # 9 TCs 2 LCs and each are int16_t
PLC_LC_DATA_SIZE = 3 * 2 # 3 LCs all int16_t
PLC_PT_DATA_SIZE = 7 * 2 # 8 PTs and each are int16_t
PLC_VALVE_DATA_SIZE = 24 # 14 valves and each are int8_t

# Class Definitions ===============================================================================
@dataclass
class PlcData():
    tc_data: bytes
    lc_data: bytes
    pt_data: bytes
    valve_data: bytes

class PlcHandler():
    def __init__(self, plc_workq: mp.Queue):
        PlcHandler.socket = socket(AF_INET, SOCK_STREAM)
        PlcHandler.socket.connect(
            (PLC_IP, PLC_PORT)
        )
        PlcHandler.plc_workq = plc_workq
        print("PLC - thread started")

    @staticmethod
    def send_command(command: bytes) -> None:
        """
        Send a command to the PLC.

        Args:
            command (bytes):
                The command to send to the PLC.
        """
        PlcHandler.socket.send(command)

    @staticmethod
    def read_response() -> Tuple[bytes]:
        tc_data = PlcHandler.socket.recv(PLC_TC_DATA_SIZE)
        if b'Unknown command' == tc_data:
            print("PLC - Unknown Command")
            return None

        lc_data = PlcHandler.socket.recv(PLC_LC_DATA_SIZE)
        pt_data = PlcHandler.socket.recv(PLC_PT_DATA_SIZE)
        valve_data = PlcHandler.socket.recv(PLC_VALVE_DATA_SIZE)

        return PlcData(tc_data, lc_data, pt_data, valve_data)

# Procedures ======================================================================================

def process_workq_message(message: WorkQCmnd, db_workq: mp.Queue) -> bool:
    """
    Process the message from the workq.

    Args:
        message (WorkQCmnd):
            The message from the workq.
        db_workq (mp.Queue):
            workq for the database.
    """
    if message.command == WorkQCmnd_e.KILL_PROCESS:
        print("PLC - Received kill command")
        return False
    elif message.command == WorkQCmnd_e.PLC_REQUEST_DATA:
        plc_command = int.to_bytes(PLC_REQUEST, 1, "little") + int.to_bytes(0, 1, "little")
        PlcHandler.send_command(plc_command)
        db_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_DATA, PlcHandler.read_response()))
    elif message.command == WorkQCmnd_e.PLC_OPEN_PBV:
        relay_num = message.data + PLC_PBV_OFFSET # Relay number to open the PBV 1 = 10, 2 = 11...
        state = 1
        plc_command = int.to_bytes(relay_num, 1, "little") + int.to_bytes(state, 1, "little")
        PlcHandler.send_command(plc_command)
    elif message.command == WorkQCmnd_e.PLC_CLOSE_PBV:
        relay_num = message.data + PLC_PBV_OFFSET # Relay number to close the PBV 1 = 10, 2 = 11...
        state = 0
        plc_command = int.to_bytes(relay_num, 1, "little") + int.to_bytes(state, 1, "little")
        PlcHandler.send_command(plc_command)
    elif message.command == WorkQCmnd_e.PLC_OPEN_SOL:
        sol_num = message.data + SOL_OFFSET # Solenoid 1 = case 21
        state = 1
        plc_command = int.to_bytes(sol_num, 1, "little") + int.to_bytes(state, 1, "little")
        PlcHandler.send_command(plc_command)
    elif message.command == WorkQCmnd_e.PLC_CLOSE_SOL:
        sol_num = message.data + SOL_OFFSET
        state = 0
        plc_command = int.to_bytes(sol_num, 1, "little") + int.to_bytes(state, 1, "little")
        PlcHandler.send_command(plc_command)
    elif message.command == WorkQCmnd_e.PLC_HEATER_ON:
        state = 1
        plc_command = int.to_bytes(PLC_HEATER_CMND, 1, "little") + int.to_bytes(state, 1, "little")
        PlcHandler.send_command(plc_command)
    elif message.command == WorkQCmnd_e.PLC_HEATER_OFF:
        state = 0
        plc_command = int.to_bytes(PLC_HEATER_CMND, 1, "little") + int.to_bytes(state, 1, "little")
        PlcHandler.send_command(plc_command)
    #TODO: Might need to add pump (PMP3) offset already listed above
    elif message.command == WorkQCmnd_e.PLC_IGN_ON:
        ign_num = message.data + PLC_IGN_OFFSET
        state = 1
        plc_command = int.to_bytes(ign_num, 1, "little") + int.to_bytes(state, 1, "little")
        PlcHandler.send_command(plc_command)
    elif message.command == WorkQCmnd_e.PLC_IGN_OFF:
        ign_num = message.data + PLC_IGN_OFFSET
        state = 0
        plc_command = int.to_bytes(ign_num, 1, "little") + int.to_bytes(state, 1, "little")
        PlcHandler.send_command(plc_command)
    return True

def plc_thread(plc_workq: mp.Queue, db_workq: mp.Queue) -> None:
    request_data = lambda: plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_REQUEST_DATA, None))

    try:
        PlcHandler(plc_workq)
        timer_stop = mp.Event()
        t = TimerThread(request_data, REQUEST_DELAY, timer_stop)
        t.start()

    except Exception as e:
        print(f"PLC - Error: {e}")
        return

    while 1:
        # If there is any workq messages, process them
        if not process_workq_message(plc_workq.get(block=True), db_workq):
            timer_stop.set()
            return