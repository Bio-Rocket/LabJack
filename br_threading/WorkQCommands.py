from enum import Enum, auto
from typing import Any


class WorkQCmnd_e(Enum):
    KILL_PROCESS = 0 # Kill the process
    HEART_BEAT = auto() # Heart beat

    COMMAND_FROM_DB = auto() # Command from the database

    LJ1_DATA = auto() # Log LabJack data to csv

    PLC_REQUEST_DATA = auto() # Request data from the PLC
    PLC_DATA = auto() # Includes TC, PT, and Valve data in a bytes tuple
    PLC_OPEN_SOL = auto() # Open the solenoid
    PLC_CLOSE_SOL = auto() # Close the solenoid

class WorkQCmnd:
    def __init__(self, command: WorkQCmnd_e, data: Any):
        self.command = command
        self.data = data