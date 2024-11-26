import multiprocessing as mp
from typing import Union
from enum import Enum, auto

from br_threading.WorkQCommands import WorkQCmnd, WorkQCmnd_e

class SystemStates(Enum):
    UNKNOWN = -1
    PRE_FIRE = 0
    TEST = auto()
    FILL = auto()
    IGNITION = auto()
    FIRE = auto()
    POST_FIRE = auto()
    ABORT = auto()

class StateMachine():
    def __init__(self, state_workq: mp.Queue, plc_workq: mp.Queue):
        self.state_workq = state_workq
        self.plc_workq = plc_workq
        self.current_state = SystemStates.PRE_FIRE
        self.manual_override = False
        self.set_default_state_positions()

    @staticmethod
    def state_transition_cmnd_to_state(state_cmnd: str) -> SystemStates:
        sys_state = None
        if state_cmnd == "GOTO_PREFIRE":
            sys_state = SystemStates.PRE_FIRE
        elif state_cmnd == "GOTO_TEST":
            sys_state = SystemStates.TEST
        elif state_cmnd == "GOTO_FILL":
            sys_state = SystemStates.FILL
        elif state_cmnd == "GOTO_IGNITION":
            sys_state = SystemStates.IGNITION
        elif state_cmnd == "GOTO_FIRE":
            sys_state = SystemStates.FIRE
        elif state_cmnd == "GOTO_POSTFIRE":
            sys_state = SystemStates.POST_FIRE
        elif state_cmnd == "GOTO_ABORT":
            sys_state = SystemStates.ABORT
        else:
            sys_state = SystemStates.UNKNOWN
        return sys_state

    @staticmethod
    def is_valid_transition(last_state: SystemStates, next_state: SystemStates) -> bool:
        """
        Check if the transition to the new state is valid.

        Args:
            new_state (SystemStates):
                The new state to transition to.
        """
        if next_state == SystemStates.UNKNOWN:
            return False

        if last_state == SystemStates.PRE_FIRE:
            if next_state == SystemStates.TEST or next_state == SystemStates.FILL:
                return True

        elif last_state == SystemStates.TEST:
            if next_state == SystemStates.PRE_FIRE:
                return True

        elif last_state == SystemStates.FILL:
            if next_state == SystemStates.PRE_FIRE or next_state == SystemStates.IGNITION or next_state == SystemStates.ABORT:
                return True

        elif last_state == SystemStates.IGNITION:
            if next_state == SystemStates.FILL or next_state == SystemStates.FIRE or next_state == SystemStates.ABORT:
                return True

        elif last_state == SystemStates.FIRE:
            if next_state == SystemStates.POST_FIRE or next_state == SystemStates.ABORT:
                return True

        elif last_state == SystemStates.POST_FIRE:
            if next_state == SystemStates.ABORT:
                return True

        elif last_state == SystemStates.ABORT:
            if next_state == SystemStates.PRE_FIRE:
                return True

        else:
            return False

    def set_default_state_positions(self):
        if self.current_state == SystemStates.PRE_FIRE:
            self.manual_override = False
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 1))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 2))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 3))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 4))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 5))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 6))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 7))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 8))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_PUMP_OFF, 3))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_SOL, 12))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_SOL, 13))
        if self.current_state == SystemStates.TEST:
            self.manual_override = True
            # All valves can be in any position by default (Note this will just be the previous state (Pre-Fire))
        if self.current_state == SystemStates.FILL:
            self.manual_override = True
            # Note this will just be the previous state (Pre-Fire) bit with manual override
        if self.current_state == SystemStates.IGNITION:
            self.manual_override = False
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 1))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 2))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 3))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 4))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 5))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 6))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 7))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 8))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_PUMP_OFF, 3))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_SOL, 12))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_SOL, 13))
        if self.current_state == SystemStates.FIRE:
            self.manual_override = False
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 5))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 6))
        if self.current_state == SystemStates.POST_FIRE:
            self.manual_override = True
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 5))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 6))
        if self.current_state == SystemStates.ABORT:
            self.manual_override = False
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 1))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 2))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 3))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 4))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 5))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 6))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 7))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 8))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_PUMP_OFF, 3))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_SOL, 12))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_SOL, 13))

    def handle_valve_change(self, command: str) -> None:
        """
        Check the valve change command from the database and send the work queue command
        that should be sent to the plc if it is a valid command.

        Args:
            command (str):
                The command from the database.
        """

        # First handle the commands that do not require a certain state to occur
        if command == "IGN1_ON":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd(WorkQCmnd_e.PLC_IGN_ON, 1)))
        elif command == "IGN1_OFF":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd(WorkQCmnd_e.PLC_IGN_OFF, 1)))
        elif command == "IGN2_ON":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd(WorkQCmnd_e.PLC_IGN_ON, 2)))
        elif command == "IGN2_OFF":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd(WorkQCmnd_e.PLC_IGN_OFF, 2)))
        elif command == "HEATER_ON":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd(WorkQCmnd_e.PLC_HEATER_ON, None)))
        elif command == "HEATER_OFF":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd(WorkQCmnd_e.PLC_HEATER_OFF, None)))

        # Check if manual override is enabled
        if not self.current_state.manual_override:
            return None

        # Handle the commands that require a certain state to occur
        if command == "PBV1_OPEN":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 1)))
        elif command == "PBV2_OPEN":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 2)))
        elif command == "PBV3_OPEN":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 3)))
        elif command == "PBV4_OPEN":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 4)))
        elif command == "PBV5_OPEN":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 5)))
        elif command == "PBV6_OPEN":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 6)))
        elif command == "PBV7_OPEN":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 7)))
        elif command == "PBV8_OPEN":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 8)))
        elif command == "PMP3_ON":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd(WorkQCmnd_e.PLC_PUMP_ON, 3)))
        elif command == "SOL12_OPEN":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_SOL, 12)))
        elif command == "SOL13_OPEN":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_SOL, 13)))
        elif command == "PBV1_CLOSE":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 1)))
        elif command == "PBV2_CLOSE":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 2)))
        elif command == "PBV3_CLOSE":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 3)))
        elif command == "PBV4_CLOSE":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 4)))
        elif command == "PBV5_CLOSE":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 5)))
        elif command == "PBV6_CLOSE":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 6)))
        elif command == "PBV7_CLOSE":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 7)))
        elif command == "PBV8_CLOSE":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 8)))
        elif command == "PMP3_OFF":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd(WorkQCmnd_e.PLC_PUMP_OFF, 3)))
        elif command == "SOL12_CLOSE":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_SOL, 12)))
        elif command == "SOL13_CLOSE":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_SOL, 13)))

    def attempt_transition(self, new_state_cmd: str) -> bool:
        """
        Attempt to transition to a new state.

        Args:
            new_state (string):
                The new state to transition to.
        """

        next_state = StateMachine.state_transition_cmnd_to_state(new_state_cmd)
        if next_state is SystemStates.UNKNOWN:
            print(f"SM - Invalid transition command: {new_state_cmd}")
            return False

        if StateMachine.is_valid_transition(self.current_state, next_state):
            self.current_state = next_state
            self.set_default_state_positions()
            print(f"SM - In state: {next_state}")
            return True
        else:
            print(f"SM - Invalid transition command: from {self.current_state} to {next_state}")
            return False

def state_thread(state_workq: mp.Queue, plc_workq: mp.Queue):
    """
    Start the state machine which controls the valve states and
    the manual value states.

    Args:
        state_workq (mp.Queue):
            The work queue for the state machine, primarily for
            a state change request.
    """
    state_machine = StateMachine(state_workq, plc_workq)

    while 1:
        message: WorkQCmnd = state_workq.get(block=True)

        if message.command == WorkQCmnd_e.KILL_PROCESS:
            print("SM - Received kill command")
            return
        elif message.command == WorkQCmnd_e.STATE_TRANSITION:
            # Attempt to transition to the new state
            state_machine.attempt_transition(message.data)
        elif message.command == WorkQCmnd_e.STATE_HANDLE_VALVE_COMMAND:
            # Process the command from the database
            # determine if the command is valid
            state_machine.handle_valve_change(message.data)
