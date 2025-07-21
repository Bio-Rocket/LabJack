import multiprocessing as mp

from StateTruth import StateTruth, SystemStates
from br_threading.WorkQCommands import WorkQCmnd, WorkQCmnd_e

class StateMachine():
    def __init__(self, state_workq: mp.Queue, t7_pro_workq: mp.Queue, plc_workq: mp.Queue, database_workq: mp.Queue):
        """
        Initialize the state machine with the work queues.
        Args:
            state_workq (mp.Queue):
                The work queue for the state machine, primarily for
                a state change request.
            t7_pro_workq (mp.Queue):
                The main work queue for the state machine, used to
                send commands about what logging speed we should be using
                for the LabJack.
            plc_workq (mp.Queue):
                The work queue for the PLC commands.
            database_workq (mp.Queue):
                The work queue for the database commands.
        """
        self.state_workq = state_workq
        self.t7_pro_workq = t7_pro_workq
        self.plc_workq = plc_workq
        self.db_workq = database_workq
        self.manual_override = False

        current_state = StateTruth.get_state()
        self.db_workq.put(WorkQCmnd(WorkQCmnd_e.DB_STATE_CHANGE, current_state.name))

        self.set_valve_for_state(current_state)

    @staticmethod
    def state_transition_cmnd_to_state(state_cmnd: str) -> SystemStates:
        sys_state = None
        if state_cmnd == "GOTO_TEST":
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

    def set_valve_for_state(self, state: SystemStates) -> None:
        """
        Set the default state positions for the valves and pumps based on the current state.

        Args:
            state (SystemStates):
                The current state of the system that the valves need to be changed to.
        """
        if state == SystemStates.ABORT:
            self.manual_override = False
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 1))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 2))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 3))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 4))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 5))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 6))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 7))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 8))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 9))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 10))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 11))

            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_SOL, 1))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_SOL, 2))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_SOL, 3))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_SOL, 4))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_SOL, 5))

        if state == SystemStates.TEST:
            self.manual_override = True

        if state == SystemStates.FILL:
            self.manual_override = True

        if state == SystemStates.IGNITION:
            self.manual_override = False
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 1))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 2))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 3))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 4))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 5))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 6))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 7))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 8))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 9))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 10))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 11))

            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_SOL, 1))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_SOL, 2))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_SOL, 3))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_SOL, 4))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_SOL, 5))

        if state == SystemStates.FIRE:
            self.manual_override = False
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 6))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 7))

            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 10))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 11))

        if state == SystemStates.POST_FIRE:
            self.manual_override = True
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 6))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 7))

            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 10))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 11))

    def update_labjack_logging(self, state: SystemStates) -> None:
        """
        Update the LabJack logging speed based on the current state.

        Args:
            state (SystemStates):
                The current state of the system.
        """
        if state == SystemStates.TEST or state == SystemStates.ABORT:
            self.t7_pro_workq.put(WorkQCmnd(WorkQCmnd_e.LJ_SLOW_LOGGING, None))
        else:
            self.t7_pro_workq.put(WorkQCmnd(WorkQCmnd_e.LJ_FAST_LOGGING, None))

    def handle_valve_change(self, command: str) -> None:
        """
        Check the valve change command from the database and send the work queue command
        that should be sent to the plc if it is a valid command.

        Args:
            command (str):
                The command from the database.
        """
        print(f"SM - Handle Valve Change: {command}")

        # First handle the commands that do not require a certain state to occur
        if command == "IGN1_ON":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_IGN_ON, 1))
        elif command == "IGN1_OFF":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_IGN_OFF, 1))
        elif command == "IGN2_ON":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_IGN_ON, 2))
        elif command == "IGN2_OFF":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_IGN_OFF, 2))

        # Check if manual override is enabled
        if not self.manual_override:
            return None

        # Handle the commands that require a certain state to occur
        if command == "PBV1_OPEN":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 1))
        elif command == "PBV2_OPEN":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 2))
        elif command == "PBV3_OPEN":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 3))
        elif command == "PBV4_OPEN":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 4))
        elif command == "PBV5_OPEN":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 5))
        elif command == "PBV6_OPEN":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 6))
        elif command == "PBV7_OPEN":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 7))
        elif command == "PBV8_OPEN":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 8))
        elif command == "PBV9_OPEN":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 9))
        elif command == "PBV10_OPEN":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 10))
        elif command == "PBV11_OPEN":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 11))

        elif command == "SOL1_OPEN":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_SOL, 1))
        elif command == "SOL2_OPEN":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_SOL, 2))
        elif command == "SOL3_OPEN":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_SOL, 3))
        elif command == "SOL4_OPEN":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_SOL, 4))
        elif command == "SOL5_OPEN":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_SOL, 5))

        elif command == "PBV1_CLOSE":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 1))
        elif command == "PBV2_CLOSE":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 2))
        elif command == "PBV3_CLOSE":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 3))
        elif command == "PBV4_CLOSE":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 4))
        elif command == "PBV5_CLOSE":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 5))
        elif command == "PBV6_CLOSE":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 6))
        elif command == "PBV7_CLOSE":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 7))
        elif command == "PBV8_CLOSE":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 8))
        elif command == "PBV9_CLOSE":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 9))
        elif command == "PBV10_CLOSE":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 10))
        elif command == "PBV11_CLOSE":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 11))

        elif command == "SOL1_CLOSE":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_SOL, 1))
        elif command == "SOL2_CLOSE":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_SOL, 2))
        elif command == "SOL3_CLOSE":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_SOL, 3))
        elif command == "SOL4_CLOSE":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_SOL, 4))
        elif command == "SOL5_CLOSE":
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_SOL, 5))

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

        current_state = StateTruth.get_state()

        if next_state == current_state:
            print(f"SM - Already in state: {next_state}")
            self.db_workq.put(WorkQCmnd(WorkQCmnd_e.DB_STATE_CHANGE, current_state.name))
            return True

        if StateTruth.change_state(next_state):
            current_state = StateTruth.get_state()
            if next_state != current_state:
                print(f"SM - State change failed: {current_state} to {next_state}")
                return False

            self.update_labjack_logging(current_state)
            self.set_valve_for_state(current_state)
            self.db_workq.put(WorkQCmnd(WorkQCmnd_e.DB_STATE_CHANGE, current_state.name))
            print(f"SM - In state: {current_state}")
            return True
        else:
            print(f"SM - Invalid transition command: from {current_state} to {next_state}")
            return False

def state_thread(state_workq: mp.Queue, t7_pro_workq: mp.Queue, plc_workq: mp.Queue, database_workq: mp.Queue):
    """
    Start the state machine which controls the valve states and
    the manual value states.

    Args:
        state_workq (mp.Queue):
            The work queue for the state machine, primarily for
            a state change request.
        t7_pro_workq (mp.Queue):
            The main work queue for the state machine, used to
            send commands about what logging speed we should be using
            for the LabJack.
        plc_workq (mp.Queue):
            The work queue for the PLC commands.
        database_workq (mp.Queue):
            The work queue for the database commands.
    """
    state_machine = StateMachine(state_workq, t7_pro_workq, plc_workq, database_workq)
    print("SM - thread started")

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
