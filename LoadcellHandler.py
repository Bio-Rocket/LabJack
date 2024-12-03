# General imports =================================================================================
from enum import Enum
from typing import Dict, Tuple

# Project specific imports ========================================================================
from br_threading.WorkQCommands import WorkQCmnd, WorkQCmnd_e

# Class Definitions ===============================================================================
class LoadCell():
    class State(Enum):
        CONVERT_MASS = 0
        WAIT_FOR_CALI_VOLTAGE = 1
        WAIT_FOR_TARE_MASS = 2
        WAIT_FOR_FINALE_VOLTAGE = 3

    def __init__(self, load_cell_name: str):
        self.load_cell_name = load_cell_name
        self.reset_loadcell()

    def reset_loadcell(self):
        """
        Reset the load cell
        """
        self.tare_offset = 0
        self.cali_slope = 1
        self.state = self.State.CONVERT_MASS
        self.y_intercept = 0

        self.calibration_points = []

    def set_calibration(self, slope: float, intercept: float):
        """
        Set the calibration slope and intercept to the given value
        """
        self.cali_slope = slope
        self.y_intercept = intercept

    def cancel_new_calibration(self):
        """
        If a cancel calibration command is received from the DB
        discard the current calibration points
        """
        self.calibration_points = []
        self.state = self.State.CONVERT_MASS

    def add_calibration_mass(self, mass: float, final_mass: bool = False):
        """
        Add a calibration point to the local slope
        and puts the load cell handler into a wait state
        to wait for a voltage that matches the mass
        """

        self.current_cali_mass = mass
        if final_mass:
            self.state = self.State.WAIT_FOR_FINALE_VOLTAGE
        else:
            self.state = self.State.WAIT_FOR_CALI_VOLTAGE

    def consume_incoming_voltage(self, raw_voltage: float) -> float:
        """
        Convert the raw voltage to a mass value or add a calibration
        point based on the current state
        """
        if self.state == self.State.CONVERT_MASS:
            pass
        elif self.state == self.State.WAIT_FOR_CALI_VOLTAGE:
            self._add_calibration_voltage(raw_voltage)
        elif self.state == self.State.WAIT_FOR_TARE_MASS:
            self.tare_offset = self._convert_voltage_to_mass(raw_voltage, with_tare=False)
            self.state = self.State.CONVERT_MASS
        elif self.state == self.State.WAIT_FOR_FINALE_VOLTAGE:
            self._add_calibration_voltage(raw_voltage)
            self.finalize()

        # This function will always return mass, even while calibrating
        # if calibrating the mass will use the previous/current slope instead
        # of the one being calculated.
        return self._convert_voltage_to_mass(raw_voltage)

    def finalize(self):
        """
        Perform final calculations for calibration and update the slope
        used to calculate the slope used by the load cell to get corrected mass.
        """

        if not self.calibration_points:
            print("Trying to finalize load cell calibration without any calibration points")
            return

        self.tare_offset = 0

        masses = [x[0] for x in self.calibration_points]
        voltages = [x[1] for x in self.calibration_points]

        mass_mean = sum(masses) / len(masses)
        voltage_mean = sum(voltages) / len(voltages)
        numerator = sum((mass - mass_mean) * ((voltage) - voltage_mean) for mass, voltage in zip(masses, voltages))
        denominator = sum((voltage - voltage_mean) ** 2 for voltage in voltages)
        slope = numerator/ denominator

        self.y_intercept = masses[0] - slope * voltages[0]
        self.set_calibration(slope, self.y_intercept)
        self.calibration_points = []
        self.state = self.State.CONVERT_MASS

    def tare_mass(self):
        """
        Set the tare offset value to the current mass
        """
        self.state = self.State.WAIT_FOR_TARE_MASS

    def _convert_voltage_to_mass(self, raw_voltage: float, with_tare: bool = True) -> float:
        """
        Convert the raw voltage from the serial handler
        to a mass value to send to the database.

        Parameters:
            voltage (float):
                The voltage reading to be calibrated.

        Returns:
            float:
                The calibrated weight corresponding to the voltage reading.
        """
        if with_tare:
            return (raw_voltage * self.cali_slope) + self.y_intercept - self.tare_offset
        else:
            return (raw_voltage * self.cali_slope) + self.y_intercept

    def _add_calibration_voltage(self, voltage: float):
        """
        Add a calibration point to for the voltage received
        to match the last calibration mass,
        and puts the load cell handler into the convert mass state
        without updating the slope
        """
        self.calibration_points.append((self.current_cali_mass, voltage))
        self.current_cali_mass = 0
        self.state = self.State.CONVERT_MASS



class LoadCellHandler():
    loadCells: Dict[str, LoadCell]

    def __init__(self):
        self.loadCells = {}

    def add_load_cell(self, key: str, slope: float = 1, intercept: float = 0):
        """
        Add a load cell to the handler

        Args:
            key (str):
                The name of the load cell being added (should match schema)
            slope (float):
                The slope of the load cell if a calibration has been previously stored.
            intercept (float):
                The intercept of the load cell if a calibration has been previously stored.
        """
        self.loadCells[key] = LoadCell(key)
        self.loadCells[key].set_calibration(slope, intercept)

    def tare_load_cell(self, key: str):
        """
        Tare the load cell

        Args:
            key (str):
                The name of the load cell to tare.
        """
        if key in self.loadCells:
            self.loadCells[key].tare_mass()

    def cancel_calibration(self, key: str):
        """
        Cancel the calibration of the load cell

        Args:
            key (str):
                The name of the load cell to cancel the calibration of.
        """
        if key in self.loadCells:
            self.loadCells[key].cancel_new_calibration()

    def add_calibration_mass(self, key: str, mass: float, final_mass: bool = False):
        """
        Add a calibration mass to the load cell

        Args:
            key (str):
                The name of the load cell to add the calibration mass to.
            mass (float):
                The mass to add to the calibration.
            final_mass (bool):
                If the mass is the final mass to calibrate the load cell.
        """
        if key in self.loadCells:
            self.loadCells[key].add_calibration_mass(mass, final_mass)

    def consume_incoming_voltage(self, key: str, raw_voltage: float) -> float:
        """
        Convert the raw voltage to a mass value

        Args:
            key (str):
                The name of the load cell to convert the voltage for.
            raw_voltage (float):
                The raw voltage to convert to a mass value.

        Returns:
            float:
                The mass value corresponding to the voltage.
        """
        if key in self.loadCells:
            return self.loadCells[key].consume_incoming_voltage(raw_voltage)
        else:
            return 0

    def get_calibration(self, key: str) -> Tuple[float, float]:
        """
        Get the calibration values for the load cell

        Args:
            key (str):
                The name of the load cell to get the calibration values for.

        Returns:
            Tuple[float, float]:
                The slope and intercept of the load cell.
        """
        if key in self.loadCells:
            return self.loadCells[key].cali_slope, self.loadCells[key].y_intercept
        else:
            return 1, 0