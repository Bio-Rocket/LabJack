# General imports =================================================================================
import multiprocessing as mp
from socket import socket, AF_INET, SOCK_STREAM
import struct
import threading
import time
from typing import Tuple
from br_threading.WorkQCommands import WorkQCmnd, WorkQCmnd_e
from dataclasses import dataclass

# Constants ========================================================================================
PLC_IP = "192.168.8.70"
PLC_PORT = 69

REQUEST_DELAY = (1.0/4.0) # in seconds
PT_COEFFICIENT = 1000

# PLC Commands and Offsets
PLC_REQUEST = 1

PLC_PBV_OFFSET = 9
SOL_OFFSET = 20

PLC_HEATER_CMND = 30

PLC_IGN_OFFSET = 31

# PLC data sizes
PLC_TC_DATA_SIZE = 9 * 2 # 9 TCs 2 LCs and each are int16_t
PLC_LC_DATA_SIZE = 3 * 2 # 3 LCs all int16_t
PLC_PT_DATA_SIZE = 7 * 2 # 8 PTs and each are int16_t
PLC_VALVE_DATA_SIZE = 24 # 14 valves and each are int8_t

# Class Definitions ===============================================================================
@dataclass
class PlcData():
    tc_data: list
    lc_data: list
    pt_data: list
    valve_data: list
    scan_rate: float = REQUEST_DELAY

class PlcHandler():
    def __init__(self, plc_workq: mp.Queue):
        PlcHandler.socket = socket(AF_INET, SOCK_STREAM)
        PlcHandler.socket.settimeout(5)

        while not PlcHandler.connect_plc():
            if PlcHandler.socket:
                PlcHandler.socket.close()
            PlcHandler.socket = socket(AF_INET, SOCK_STREAM)
            PlcHandler.socket.settimeout(5)

        PlcHandler.plc_workq = plc_workq
        print("PLC - thread started")

    @staticmethod
    def connect_plc() -> None:
        """
        Close the connection to the PLC.
        """
        try:
            PlcHandler.socket.connect((PLC_IP, PLC_PORT))
            return True
        except Exception as e:
            print(f"PLC - Error connecting to PLC, {e}, retrying...")
            return False


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

        test_data = list(PlcHandler.socket.recv(PLC_TC_DATA_SIZE))
        print(f"ETHAN {test_data}")

        if b'Unknown command' == test_data:
            print("PLC - Unknown Command")
            return None

        tc_data = list(struct.unpack('<' + 'h' * (PLC_TC_DATA_SIZE //2),  PlcHandler.socket.recv(PLC_TC_DATA_SIZE)))
        lc_data = list(struct.unpack('<' + 'h' * (PLC_LC_DATA_SIZE //2),  PlcHandler.socket.recv(PLC_LC_DATA_SIZE)))
        pt_data = list(struct.unpack('<' + 'h' * (PLC_PT_DATA_SIZE //2),  PlcHandler.socket.recv(PLC_PT_DATA_SIZE)))
        pt_data = [x / PT_COEFFICIENT for x in pt_data]
        valve_data = list(PlcHandler.socket.recv(PLC_VALVE_DATA_SIZE))

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

def request_data_background(plc_workq: mp.Queue):
    """
    Notify DB backend is Live
    """
    while True:
        plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_REQUEST_DATA, None))
        time.sleep(REQUEST_DELAY)


def plc_thread(plc_workq: mp.Queue, db_workq: mp.Queue) -> None:
    try:
        PlcHandler(plc_workq)
    except Exception as e:
        print(f"PLC - Error: {e}")
        return

    # Start the background task in a separate thread
    background_thread = threading.Thread(target=request_data_background, args=(plc_workq,))
    background_thread.daemon = True
    background_thread.start()

    while 1:
        # If there is any workq messages, process them
        if not process_workq_message(plc_workq.get(block=True), db_workq):
            return