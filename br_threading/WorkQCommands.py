from enum import Enum, auto
from typing import Any


class WorkQCmnd_e(Enum):
    KILL_PROCESS = 0 # Kill the process

    PLC_DB_COMMAND = auto() # Command from the database
    DB_HEART_BEAT = auto() # Heart beat

    LJ_DATA = auto() # Log LabJack data to csv

    PLC_REQUEST_DATA = auto() # Request data from the PLC
    PLC_DATA = auto() # Includes TC, PT, and Valve data in a bytes tuple

    PLC_OPEN_PBV = auto() # Open the Pneumatic Ball Valve, expects the PBV number
    PLC_CLOSE_PBV = auto() # Close the Pneumatic Ball Valve, expects a PBV number

    PLC_PUMP_ON = auto() # Turn on the pump, expects the pump number
    PLC_PUMP_OFF = auto() # Turn off the pump, expects the pump number

    PLC_IGN_ON = auto() # Turn on the igniter, expects the igniter number
    PLC_IGN_OFF = auto() # Turn off the igniter, expects the igniter number

    PLC_HEATER_ON = auto() # Turn on the heater
    PLC_HEATER_OFF = auto() # Turn off the heater


class WorkQCmnd:
    def __init__(self, command: WorkQCmnd_e, data: Any):
        self.command = command
        self.data = data