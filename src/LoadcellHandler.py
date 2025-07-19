# General imports =================================================================================
import os
import numpy as np

from typing import Dict, List
import json
from pathlib import Path

# Constants ======================================================================================
EXPECTED_SCHEMA_JSON = os.path.join(Path(__file__).parents[1], "LoadCellConfig.json")

# Class Definitions ===============================================================================
class LoadCell():

    def __init__(self, load_cell_name: str):
        self.load_cell_name = load_cell_name
        self.slope = 0.0
        self.intercept = 0.0

    def set_calibration(self, voltages: List[float], weights: List[float]) -> None:
        """
        Sets the calibration data for the load cell.

        Args:
            voltages (List[float]): A list of voltage readings from the load cell.
            weights (List[float]): A list of corresponding weights for the voltage readings.
        """

        if len(voltages) != len(weights):
            print(f"LC - Calibration data poorly formatted for {self.load_cell_name}. ")
            return

        self.slope, self.intercept = np.polyfit(voltages, weights, 1)

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
                    calibration_voltages = data[lc_name].get('voltage', [])
                    calibration_weights = data[lc_name].get('weight', [])
                    self.loadCells[lc_name].set_calibration(calibration_voltages, calibration_weights)

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