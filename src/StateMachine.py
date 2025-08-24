import multiprocessing as mp
import time
from typing import Dict, Optional

from StateTruth import StateTruth, SystemStates
from br_threading.WorkQCommands import StateTransitionData, WorkQCmnd, WorkQCmnd_e

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
        self.hardware_abort = False

        current_state = StateTruth.get_state()
        valve_state_dict = StateTruth.get_valve_state_dict()

        self.set_initial_valve_for_state(current_state, valve_state_dict)
        self.publish_state(current_state)
        self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_STATE_LIGHT_COMMAND, current_state))

    def set_hardware_abort(self, enabled: bool) -> None:
        """
        Set or clear the hardware abort flag. Does NOT force the software to
        switch to ABORT; it only blocks transitions & valve/solenoid commands.
        """
        if enabled is True and not self.hardware_abort:
            print("SM - Hardware abort set")
            self.attempt_transition("GOTO_ABORT")

        self.hardware_abort = enabled
        self.publish_state(StateTruth.get_state())

    @staticmethod
    def state_transition_cmnd_to_state(state_cmnd: str) -> SystemStates:
        if state_cmnd == "GOTO_TEST":
            return SystemStates.TEST
        elif state_cmnd == "GOTO_FILL":
            return SystemStates.FILL
        elif state_cmnd == "GOTO_IGNITION":
            return SystemStates.IGNITION
        elif state_cmnd == "GOTO_FIRE":
            return SystemStates.FIRE
        elif state_cmnd == "GOTO_POSTFIRE":
            return SystemStates.POST_FIRE
        elif state_cmnd == "GOTO_ABORT":
            return SystemStates.ABORT
        else:
            return SystemStates.UNKNOWN

    def publish_state(self, state: SystemStates) -> None:
        """
        Push the current state + hardware_abort flag to the DB for UI sync.
        """
        payload = {
            "current_state": state.name,
            "hardware_abort": "true" if self.hardware_abort else "false"
        }
        self.db_workq.put(WorkQCmnd(WorkQCmnd_e.DB_STATE_CHANGE, payload))

    def set_initial_valve_for_state(self, state: SystemStates, valve_state_dict: Optional[Dict[str, bool]] = None) -> None:
        """
        Set the initial valve states based on the current state.
        This is called when the state machine is initialized.

        Args:
            state (SystemStates): The current state of the system.
            valve_state_dict (Optional[Dict[str, bool]]): A dictionary containing the state of all valves and pumps.
                If None, the default states will be set based on the current state.
                If valve_state_dict is provided, it will override the default states.
        """
        if valve_state_dict is None:
            self.set_default_valve_for_state(state)
            return

        if state == SystemStates.ABORT:
            self.manual_override = False
        elif state == SystemStates.TEST:
            self.manual_override = True
        elif state == SystemStates.FILL:
            self.manual_override = True
        elif state == SystemStates.IGNITION:
            self.manual_override = False
        elif state == SystemStates.FIRE:
            self.manual_override = False
        elif state == SystemStates.POST_FIRE:
            self.manual_override = True
        elif state == SystemStates.UNKNOWN:
            print("STATE TRUTH - Cannot set valve state for UNKNOWN state, skipping")
            return

        if valve_state_dict["PBV1"]:
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 1))
        else:
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 1))
        if valve_state_dict["PBV2"]:
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 2))
        else:
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 2))
        if valve_state_dict["PBV3"]:
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 3))
        else:
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 3))
        if valve_state_dict["PBV4"]:
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 4))
        else:
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 4))
        if valve_state_dict["PBV5"]:
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 5))
        else:
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 5))
        if valve_state_dict["PBV6"]:
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 6))
        else:
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 6))
        if valve_state_dict["PBV7"]:
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 7))
        else:
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 7))
        if valve_state_dict["PBV8"]:
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 8))
        else:
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 8))
        if valve_state_dict["PBV9"]:
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 9))
        else:
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 9))
        if valve_state_dict["PBV10"]:
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 10))
        else:
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 10))
        if valve_state_dict["PBV11"]:
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 11))
        else:
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 11))
        if valve_state_dict["SOL1"]:
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_SOL, 1))
        else:
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_SOL, 1))
        if valve_state_dict["SOL2"]:
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_SOL, 2))
        else:
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_SOL, 2))
        if valve_state_dict["SOL3"]:
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_SOL, 3))
        else:
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_SOL, 3))
        if valve_state_dict["SOL4"]:
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_SOL, 4))
        else:
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_SOL, 4))
        if valve_state_dict["SOL5"]:
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_SOL, 5))
        else:
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_SOL, 5))
        if valve_state_dict["IGN1"]:
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_IGN_ON, 1))
        else:
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_IGN_OFF, 1))
        if valve_state_dict["IGN2"]:
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_IGN_ON, 2))
        else:
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_IGN_OFF, 2))

    def set_default_valve_for_state(self, state: SystemStates, ignitor_desired_states: Optional[Dict[str, bool]] = None) -> None:
        """
        Set the default state positions for the valves and pumps based on the current state.

        Args:
            state (SystemStates): The current state of the system.
            ignitor_desired_states (Optional[Dict[str, bool]]): A dictionary containing the desired states of
        """
        if state == SystemStates.ABORT:
            self.manual_override = False
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 1))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 2)) # CLOSED IS OPEN (DEENERGIZED OPEN)
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 3))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 4)) # CLOSED IS OPEN (DEENERGIZED OPEN)
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 5)) # CLOSED IS OPEN (DEENERGIZED OPEN)
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 6))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 7))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 8))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 9)) # CLOSED IS OPEN (DEENERGIZED OPEN)
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 10))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 11))

            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_SOL, 1))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_SOL, 2))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_SOL, 3))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_SOL, 4))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_SOL, 5))

            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_IGN_OFF, 1))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_IGN_OFF, 2))

        if state == SystemStates.TEST:
            self.manual_override = True

        if state == SystemStates.FILL:
            self.manual_override = True
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_IGN_OFF, 1))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_IGN_OFF, 2))

        if state == SystemStates.IGNITION:
            self.manual_override = False
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 1))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 2)) # ENERGIZED IS CLOSED (OPEN COMMAND)
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 3))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 4)) # ENERGIZED IS CLOSED (OPEN COMMAND)
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 5)) # ENERGIZED IS CLOSED (OPEN COMMAND)
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 6))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 7))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 8))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 9)) # ENERGIZED IS CLOSED (OPEN COMMAND)
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 10))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 11))

            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_SOL, 1))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_SOL, 2))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_SOL, 3))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_SOL, 4))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_SOL, 5))

            if ignitor_desired_states is None:
                ignitor_desired_states = {"IGN1": False, "IGN2": False}
            if ignitor_desired_states.get("IGN1", False):
                self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_IGN_ON, 1))
            else:
                self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_IGN_OFF, 1))
            if ignitor_desired_states.get("IGN2", False):
                self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_IGN_ON, 2))
            else:
                self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_IGN_OFF, 2))

        if state == SystemStates.FIRE:
            self.manual_override = False
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 6))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 7))

            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 10))
            timer = mp.Process(target=lambda: (time.sleep(0.32), self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_OPEN_PBV, 11))))
            timer.start()

            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_IGN_OFF, 1))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_IGN_OFF, 2))

        if state == SystemStates.POST_FIRE:
            self.manual_override = True
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 6))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 7))

            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 10))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_CLOSE_PBV, 11))

            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_IGN_OFF, 1))
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_IGN_OFF, 2))

    def update_labjack_logging(self, state: SystemStates) -> None:
        """
        Update the LabJack logging speed based on the current state.
        """
        if state in (SystemStates.TEST, SystemStates.ABORT):
            self.t7_pro_workq.put(WorkQCmnd(WorkQCmnd_e.LJ_SLOW_LOGGING, None))
        else:
            self.t7_pro_workq.put(WorkQCmnd(WorkQCmnd_e.LJ_FAST_LOGGING, None))

    def handle_valve_change(self, command: str) -> None:
        """
        Process a valve/solenoid/ignition command coming from the DB/front-end.
        This is blocked when hardware_abort is active.
        """
        print(f"SM - Handle Valve Change: {command}")

        # BLOCK when HW abort is active
        if self.hardware_abort:
            print("SM - HW abort active: valve command blocked")
            return

        # First handle the commands that do not require a certain state to occur
        if StateTruth.get_state() in [SystemStates.IGNITION, SystemStates.TEST]:
            if command == "IGN1_ON":
                self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_IGN_ON, 1))
                return
            elif command == "IGN1_OFF":
                self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_IGN_OFF, 1))
                return
            elif command == "IGN2_ON":
                self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_IGN_ON, 2))
                return
            elif command == "IGN2_OFF":
                self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_IGN_OFF, 2))
                return

        # Check if manual override is enabled
        if not self.manual_override:
            return

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


    def attempt_transition(self, new_state_cmd: StateTransitionData) -> bool:
        """
        Attempt to transition to a new state.

        Blocks all transitions (except GOTO_ABORT) while hardware_abort is set.
        """
        next_state = StateMachine.state_transition_cmnd_to_state(new_state_cmd.state_command)
        if next_state is SystemStates.UNKNOWN:
            print(f"SM - Invalid transition command: {new_state_cmd.state_command}")
            return False

        # Block while hardware abort is active, unless going to ABORT
        if self.hardware_abort:
            print("SM - HW abort active: transition blocked")
            self.publish_state(StateTruth.get_state())
            return False

        current_state = StateTruth.get_state()

        if next_state == current_state:
            print(f"SM - Already in state: {next_state}")
            self.publish_state(current_state)
            return True

        if StateTruth.change_state(next_state):
            current_state = StateTruth.get_state()
            if next_state != current_state:
                print(f"SM - State change failed: {current_state} to {next_state}")
                return False

            self.update_labjack_logging(current_state)
            self.set_default_valve_for_state(current_state, ignitor_desired_states=new_state_cmd.ignition_stats)
            self.publish_state(current_state)
            self.plc_workq.put(WorkQCmnd(WorkQCmnd_e.PLC_STATE_LIGHT_COMMAND, current_state))
            print(f"SM - In state: {current_state}")
            return True
        else:
            print(f"SM - Invalid transition command: from {current_state} to {next_state}")
            return False

def state_thread(state_workq: mp.Queue,
                 t7_pro_workq: mp.Queue,
                 plc_workq: mp.Queue,
                 database_workq: mp.Queue):
    """
    Start the state machine which controls the valve states and manual valve states.
    """
    state_machine = StateMachine(state_workq, t7_pro_workq, plc_workq, database_workq)
    print("SM - thread started")

    while True:
        message: WorkQCmnd = state_workq.get(block=True)

        if message.command == WorkQCmnd_e.KILL_PROCESS:
            print("SM - Received kill command")
            return

        elif message.command == WorkQCmnd_e.RPI_HARDWARE_ABORT:
            print("SM - Hardware abort asserted")
            state_machine.set_hardware_abort(True)

        elif message.command == WorkQCmnd_e.RPI_HARDWARE_ABORT_CLEAR:
            print("SM - Hardware abort cleared")
            state_machine.set_hardware_abort(False)

        elif message.command == WorkQCmnd_e.STATE_TRANSITION:
            state_machine.attempt_transition(message.data)

        elif message.command == WorkQCmnd_e.STATE_HANDLE_VALVE_COMMAND:
            state_machine.handle_valve_change(message.data)
