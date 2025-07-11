from enum import Enum, auto
from typing import Any


class WorkQCmnd_e(Enum):
    KILL_PROCESS = 0 # Kill the process

    ## Internal DB Commands
    DB_GS_COMMAND = auto() # Command from the database
    DB_LC_COMMAND = auto() # Internal DB Command for the Load Cell Handler
    DB_STATE_COMMAND = auto() # Command for DB to send to the state machine
    DB_STATE_CHANGE = auto() # Change the system state in the DB
    DB_HEARTBEAT = auto() # Heartbeat
    FRONTEND_HEARTBEAT = auto() # Heartbeat from the frontend

    ## Labjack Data from LJ to the DB
    LJ_DATA = auto() # Log LabJack data to DB, expects dictionary [str: float]

    ## PLC Internal Commands
    PLC_REQUEST_DATA = auto() # Request data from the PLC (Internal PLC Command)

    ## PLC Data from PLC to the DB
    PLC_DATA = auto() # Includes TC, LC, PT, and Valve data in a PlcData object

    ## PLC Commands to adjust the valves, Pumps, Igniters, and Heater
    PLC_OPEN_PBV = auto() # Open the Pneumatic Ball Valve, expects the PBV number
    PLC_CLOSE_PBV = auto() # Close the Pneumatic Ball Valve, expects a PBV number

    PLC_OPEN_SOL = auto() # Open the Solenoid Valve, expects the Solenoid number
    PLC_CLOSE_SOL = auto() # Close the Solenoid Valve, expects the Solenoid number

    PLC_IGN_ON = auto() # Turn on the igniter, expects the igniter number
    PLC_IGN_OFF = auto() # Turn off the igniter, expects the igniter number

    ## State Machine Commands
    STATE_HANDLE_VALVE_COMMAND = auto() # Handle a valve command from the database then send to PLC if valid
    STATE_TRANSITION = auto() # Attempt to transition to a new state


class WorkQCmnd:
    def __init__(self, command: WorkQCmnd_e, data: Any):
        self.command = command
        self.data = data