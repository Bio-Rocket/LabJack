from enum import Enum, auto


class WorkQCmnd_e(Enum):
    KILL_PROCESS = 0 # Kill the process
    LJ_T7_DATA = auto() # Log LabJack data to csv

class WorkQCmnd:
    def __init__(self, command: WorkQCmnd_e, data):
        self.command = command
        self.data = data