# General imports =================================================================================
import os
import numpy as np

from typing import Dict, List
import json
from pathlib import Path

# Constants ======================================================================================
EXPECTED_SCHEMA_JSON = os.path.join(Path(__file__).parents[1], "LoadCellConfig.json")
AMPLIFIER_BOARD_MULTIPLIER = 333

# Class Definitions ===============================================================================
class LoadCell():

    def __init__(self, load_cell_name: str):
        self.load_cell_name = load_cell_name
        self.slope = 0.0
        self.intercept = 0.0
        self.calibration_voltages = [] # List of voltages in Volts
        self.calibration_weights = [] # List of weights in kg

    def set_calibration_voltages(self, voltages_mV: List[float]) -> None:
        """
        Sets the calibration voltages for the load cell.
        Convert mV to V and apply amplifier board multiplier.

        Args:
            voltages_mV (List[float]): A list of voltage readings from the load cell in millivolts.
        """
        self.calibration_voltages = [v / 1000 * AMPLIFIER_BOARD_MULTIPLIER for v in voltages_mV]

    def set_calibration_weights(self, weights_lbs: List[float]) -> None:
        """
        Sets the calibration weights for the load cell.
        Convert lbs to kg.

        Args:
            weights (List[float]): A list of corresponding weights for the voltage readings in lbs.
        """
        self.calibration_weights = [w / 2.2 for w in weights_lbs]

    def apply_reference_voltage(self, ref_voltage: float) -> None:
        """
        Applies the reference voltage to the load cell voltage calibrations.
        This is used to adjust the calibration data based on the reference voltage.

        Args:
            ref_voltage (float): The reference voltage in Volts.
        """
        if ref_voltage <= 0:
            print(f"LC - Invalid reference voltage {ref_voltage} for {self.load_cell_name}.")
            return

        self.calibration_voltages = [v * ref_voltage / 10 for v in self.calibration_voltages]

    def set_calibration(self) -> None:
        """
        Sets the calibration data for the load cell.

        Args:
            voltages (List[float]): A list of voltage readings from the load cell.
            weights (List[float]): A list of corresponding weights for the voltage readings.
        """

        if len(self.calibration_voltages) != len(self.calibration_weights):
            print(f"LC - Calibration data poorly formatted for {self.load_cell_name}. ")
            return

        self.slope, self.intercept = np.polyfit(self.calibration_voltages, self.calibration_weights, 1)

    def convert_voltage_to_mass(self, raw_voltage: float) -> float:
        """
        Converts a raw voltage reading from the load cell to a mass value using the calibration data.

        Args:
            raw_voltage (float): The raw voltage reading from the load cell.

        Returns:
            float: The calculated mass value based on the calibration data.
        """
        if self.slope == 0.0 and self.intercept == 0.0:
            print(f"LC - Load cell {self.load_cell_name} has not been calibrated.")
            return -999
        return raw_voltage * self.slope + self.intercept

class LoadCellHandler():
    loadCells: Dict[str, LoadCell]

    def __init__(self):
        """Initializes the LoadCellHandler and loads the load cell configurations from a JSON file."""
        self.loadCells = {}
        try:
            with open(EXPECTED_SCHEMA_JSON, 'r') as f:
                data = json.load(f)
                for lc_name in data:
                    self.loadCells[lc_name] = LoadCell(lc_name)
                    self.loadCells[lc_name].set_calibration_voltages(data[lc_name].get('voltage', []))
                    self.loadCells[lc_name].set_calibration_weights(data[lc_name].get('weight', []))
                    self.loadCells[lc_name].set_calibration()
        except Exception as e:
            print(f"LC - Error loading LoadCellConfig file: {e}")

    def convert_raw_voltage(self, load_cell_name: str, raw_voltage: float) -> float:
        """Returns the LoadCell object for the given load cell name.

        Args:
            load_cell_name (str): The name of the load cell to retrieve.
            raw_voltage (float): The raw voltage reading from the load cell.

        Returns:
            float: The calculated mass value based on the
            calibration data of the specified load cell.
        """
        if load_cell_name not in self.loadCells:
            print(f"LC - Load cell {load_cell_name} does not exist.")

        return self.loadCells[load_cell_name].convert_voltage_to_mass(raw_voltage)

    def apply_reference_voltage(self, ref_voltage: float) -> None:
        """
        Applies the reference voltage to all load cells in the handler.

        Args:
            ref_voltage (float):
                The reference voltage in Volts.
        """
        for lc in self.loadCells.values():
            lc.apply_reference_voltage(ref_voltage)
            lc.set_calibration()