# NOTE: THIS FILE IS ONLY USED FOR STATIC FIRE AND COLD FLOW.
#       THE STATE WILL NORMALLY BE HANDLED BY THE DMB ON THE ROCKET.

from dataclasses import dataclass
from enum import Enum, auto
import pickle
from typing import Any, Dict, Optional

LAST_STATE_FILE = "last_state.pkl"
class SystemStates(Enum):
    UNKNOWN = -1
    TEST = 0
    FILL = auto()
    IGNITION = auto()
    FIRE = auto()
    POST_FIRE = auto()
    ABORT = auto()

@dataclass
class LastState:
    system_state: SystemStates
    PBV1: bool
    PBV2: bool
    PBV3: bool
    PBV4: bool
    PBV5: bool
    PBV6: bool
    PBV7: bool
    PBV8: bool
    PBV9: bool
    PBV10: bool
    PBV11: bool
    SOL1: bool
    SOL2: bool
    SOL3: bool
    SOL4: bool
    SOL5: bool
    IGN1: bool
    IGN2: bool

# TODO: Will need to add a wrapper so that this can work with embedded or static mode.

class StateTruth:
    current_state: Dict[str, Any]

    @classmethod
    def init_state_truth(cls, shared_dict: Any) -> None:
        """
        Initialize the static state of the system.
        This method sets the initial state to ABORT.
        """
        # Check first to see if there is a state file to recover from.
        try:
            with open(LAST_STATE_FILE, "rb") as f:
                loaded_state: LastState = pickle.load(f)
                shared_dict["state"] = loaded_state.system_state
                shared_dict["PBV1"] = loaded_state.PBV1
                shared_dict["PBV2"] = loaded_state.PBV2
                shared_dict["PBV3"] = loaded_state.PBV3
                shared_dict["PBV4"] = loaded_state.PBV4
                shared_dict["PBV5"] = loaded_state.PBV5
                shared_dict["PBV6"] = loaded_state.PBV6
                shared_dict["PBV7"] = loaded_state.PBV7
                shared_dict["PBV8"] = loaded_state.PBV8
                shared_dict["PBV9"] = loaded_state.PBV9
                shared_dict["PBV10"] = loaded_state.PBV10
                shared_dict["PBV11"] = loaded_state.PBV11
                shared_dict["SOL1"] = loaded_state.SOL1
                shared_dict["SOL2"] = loaded_state.SOL2
                shared_dict["SOL3"] = loaded_state.SOL3
                shared_dict["SOL4"] = loaded_state.SOL4
                shared_dict["SOL5"] = loaded_state.SOL5
                shared_dict["IGN1"] = loaded_state.IGN1
                shared_dict["IGN2"] = loaded_state.IGN2
        except Exception as e:
            print(f"Error loading last state: {e}")
            shared_dict["state"] = SystemStates.ABORT
            # Initialize the shared state dictionary
            shared_dict["PBV1"] = False
            shared_dict["PBV2"] = False
            shared_dict["PBV3"] = False
            shared_dict["PBV4"] = False
            shared_dict["PBV5"] = False
            shared_dict["PBV6"] = False
            shared_dict["PBV7"] = False
            shared_dict["PBV8"] = False
            shared_dict["PBV9"] = False
            shared_dict["PBV10"] = False
            shared_dict["PBV11"] = False
            shared_dict["SOL1"] = False
            shared_dict["SOL2"] = False
            shared_dict["SOL3"] = False
            shared_dict["SOL4"] = False
            shared_dict["SOL5"] = False
            shared_dict["IGN1"] = False
            shared_dict["IGN2"] = False

        cls.current_state = shared_dict
        cls.save_current_state()

    @classmethod
    def save_current_state(cls) -> None:
        """
        Save the current state to a file.
        This method saves the current state to a file for recovery.
        """
        last_state = LastState(
            system_state=cls.current_state.get("state", SystemStates.UNKNOWN),
            PBV1=cls.current_state.get("PBV1", False),
            PBV2=cls.current_state.get("PBV2", False),
            PBV3=cls.current_state.get("PBV3", False),
            PBV4=cls.current_state.get("PBV4", False),
            PBV5=cls.current_state.get("PBV5", False),
            PBV6=cls.current_state.get("PBV6", False),
            PBV7=cls.current_state.get("PBV7", False),
            PBV8=cls.current_state.get("PBV8", False),
            PBV9=cls.current_state.get("PBV9", False),
            PBV10=cls.current_state.get("PBV10", False),
            PBV11=cls.current_state.get("PBV11", False),
            SOL1=cls.current_state.get("SOL1", False),
            SOL2=cls.current_state.get("SOL2", False),
            SOL3=cls.current_state.get("SOL3", False),
            SOL4=cls.current_state.get("SOL4", False),
            SOL5=cls.current_state.get("SOL5", False),
            IGN1=cls.current_state.get("IGN1", False),
            IGN2=cls.current_state.get("IGN2", False)
        )
        with open(LAST_STATE_FILE, "wb") as f:
            pickle.dump(last_state, f)

    @classmethod
    def get_state(cls) -> SystemStates:
        """
        Get the current state of the system.

        Returns:
            SystemStates: The current state of the system.
            If not initialized, returns SystemStates.UNKNOWN.
        """
        if "state" not in cls.current_state:
            cls.current_state["state"] = SystemStates.UNKNOWN
        return cls.current_state["state"]

    @classmethod
    def set_valve_state(cls, valve: str, valve_state: bool) -> None:
        """
        Set the state of a valve in the system.

        Args:
            valve (str):
                The name of the valve to set.
            valve_state (bool):
                The state to set the valve to.
                (energized = true or de-energized = false)
        """
        if valve not in cls.current_state:
            print(f"STATE TRUTH - Invalid valve name provided <{valve}>, cannot set state.")

        cls.current_state[valve] = valve_state
        cls.save_current_state()

    @classmethod
    def get_valve_state_dict(cls) -> Optional[Dict[str, Any]]:
        """
        Set the state of a valve in the system.

        Returns:
            Optional[Dict[str, Any]]: A dictionary containing the state of all valves and pumps
            or None if the state has not been initialized.
        """
        if cls.current_state is None:
            print("STATE TRUTH - HAS NOT BEEN INITIALIZED.")
            return None
        return cls.current_state


    @classmethod
    def change_state(cls, next_state: SystemStates) -> bool:
        """
        Check if the transition to the new state is
        valid and perform the state change if valid.

        Args:
            new_state (SystemStates):
                The new state to transition to.

        Returns:
            bool: True if the transition occurred, False otherwise.
        """
        # Cannot go to UNKNOWN state on purpose
        if next_state == SystemStates.UNKNOWN:
            return False

        current_state = cls.get_state()

        if current_state == SystemStates.ABORT:
            if next_state == SystemStates.FILL or next_state == SystemStates.TEST:
                cls.current_state["state"] = next_state
                cls.save_current_state()
                return True
        elif current_state == SystemStates.TEST:
            if next_state == SystemStates.ABORT:
                cls.current_state["state"] = next_state
                cls.save_current_state()
                return True
        elif current_state == SystemStates.FILL:
            if next_state == SystemStates.IGNITION or next_state == SystemStates.ABORT:
                cls.current_state["state"] = next_state
                cls.save_current_state()
                return True
        elif current_state == SystemStates.IGNITION:
            if next_state == SystemStates.FILL or next_state == SystemStates.FIRE or next_state == SystemStates.ABORT:
                cls.current_state["state"] = next_state
                cls.save_current_state()
                return True
        elif current_state == SystemStates.FIRE:
            if next_state == SystemStates.POST_FIRE or next_state == SystemStates.ABORT:
                cls.current_state["state"] = next_state
                cls.save_current_state()
                return True
        elif current_state == SystemStates.POST_FIRE:
            if next_state == SystemStates.FILL or next_state == SystemStates.ABORT:
                cls.current_state["state"] = next_state
                cls.save_current_state()
                return True

        return False

