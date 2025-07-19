# NOTE: THIS FILE IS ONLY USED FOR STATIC FIRE AND COLD FLOW.
#       THE STATE WILL NORMALLY BE HANDLED BY THE DMB ON THE ROCKET.

from multiprocessing.managers import DictProxy
from enum import Enum, auto
from typing import Any, Dict


class SystemStates(Enum):
    UNKNOWN = -1
    TEST = 0
    FILL = auto()
    IGNITION = auto()
    FIRE = auto()
    POST_FIRE = auto()
    ABORT = auto()

# TODO: Will need to add a wrapper so that this can work with embedded or static mode.

class StateTruth:
    current_state: Dict[str, Any]

    @classmethod
    def init_state_truth(cls, shared_dict: Any) -> None:
        """
        Initialize the static state of the system.
        This method sets the initial state to ABORT.
        """
        cls.current_state = shared_dict

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
                return True
        elif current_state == SystemStates.TEST:
            if next_state == SystemStates.ABORT:
                cls.current_state["state"] = next_state
                return True
        elif current_state == SystemStates.FILL:
            if next_state == SystemStates.IGNITION or next_state == SystemStates.ABORT:
                cls.current_state["state"] = next_state
                return True
        elif current_state == SystemStates.IGNITION:
            if next_state == SystemStates.FILL or next_state == SystemStates.FIRE or next_state == SystemStates.ABORT:
                cls.current_state["state"] = next_state
                return True
        elif current_state == SystemStates.FIRE:
            if next_state == SystemStates.POST_FIRE or next_state == SystemStates.ABORT:
                cls.current_state["state"] = next_state
                return True
        elif current_state == SystemStates.POST_FIRE:
            if next_state == SystemStates.FILL or next_state == SystemStates.ABORT:
                cls.current_state["state"] = next_state
                return True

        return False

