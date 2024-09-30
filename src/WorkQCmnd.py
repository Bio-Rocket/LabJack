from enum import Enum, auto
from typing import Any


class WorkQCmnd_e(Enum):
    KILL_PROCESS = 0 # Kill the process
    LJ_T7_DATA = auto() # Log LabJack data to csv
    HEART_BEAT = auto() # Heart beat

class WorkQCmnd:
    def __init__(self, command: WorkQCmnd_e, data: Any):
        self.command = command
        self.data = data