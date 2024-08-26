"""""""""""""""""""""""""""""""""""""""""""""
LabJackInterface.py

This file contains a wrapper for LabJack T-Series devices using the LabJack LJM library.

Classes:
- LabJack: Wrapper for the LabJack device, 
    for initialization, and any device wide functions (e.g. stream start/stop)
- AnalogInput: Wrapper for analog input channels, 
    for setting the range, resolution, and reading the value for AIN channels
- AnalogOutput: Wrapper for analog output channels,
    for writing a voltage to the DAC channels
- DigitalInput: Wrapper for digital input channels,
    for reading the value on DIO channels (includes FIO/EIO/CIO/MIO)
- DigitalOutput: Wrapper for digital output channels,
    for writing a value to DIO channels (includes FIO/EIO/CIO/MIO)

@author: Christopher Chan (cjchanx)
@date: 2023-10-12
@version: 0.1
"""""""""""""""""""""""""""""""""""""""""""""
from modified_ljm import ljm
import sys, time

# Constants for configuration
DEFAULT_STREAM_RESOLUTION = 1

# Constants from LabJack Data Sheets
MAX_SAMPLES_PER_PACKET_USB = 24
MAX_SAMPLES_PER_PACKET_ETH = 512

class LabJack:
    def __init__(self, device, connection, identifier = "ANY"):
        """
        Initialize the LabJack object
        @param device: Device type, e.g. "T7", "T4", "T8"
        @param connection: Connection type, e.g. "USB", "ETHERNET", "WIFI"
        @param identifier: Device identifier, e.g. "ANY", "<serial number>", "<IP address>"
        """
        self.handle = ljm.openS(device, connection, identifier)
        self.info = ljm.getHandleInfo(self.handle)

        self. dacMaxVolts = 10 # Note: Modify to 5V for T4/7
        
        if self.is_streaming():
            self.stop_stream()

    def close(self):
        ljm.close(self.handle)
        self.handle = 0

    def start_stream(self, scan_list, scan_rate, scans_per_read = None, callback = None, obj = None, workq = None, stream_resolution_index : int = DEFAULT_STREAM_RESOLUTION, settling_us : float = 0):
        """
        Start a stream with the given parameters.
        @assumptions ADC range and resolution have been configured.

        @param scan_list: List of scan names, e.g. ["AIN0", "AIN1"]
        @param scan_rate: Desired scan rate in Hz
        @param scans_per_read: Number of scans per read, if not specified attempts to calculate the optimal scans based on the connection type
        @param callback: Callback function for stream data, will trigger every time data is ready to be read (reached scans per read)
        @param stream_resolution_index: Resolution index for the stream for analog inputs, see
            https://support.labjack.com/docs/a-3-2-2-t7-noise-and-resolution-t-series-datasheet
            https://support.labjack.com/docs/a-3-3-2-t8-noise-and-resolution-t-series-datasheet
        @param settling_us: Settling time in microseconds, recommended to keep to 0 (automatic selection)

        @return: Actual scan rate, 0 on error

        @reference https://github.com/labjack/labjack-ljm-python/blob/master/Examples/More/Stream/stream_callback.py
        """
        # --- Input Cleaning ---
        if scan_list is None or len(scan_list) == 0 or scan_rate <= 0:
            print("\033[91mInvalid input. Please enter valid scan list and scan rate.\033[0m")
            return 0

        try:
            # --- Input Processing ---
            # Calculate scans per read
            if scans_per_read is None:
                n_channels = len(scan_list)
                scans_per_read = MAX_SAMPLES_PER_PACKET_ETH // n_channels
                if self.get_connection_type() == "USB":
                    scans_per_read = MAX_SAMPLES_PER_PACKET_USB // n_channels

            # Convert scan names to addresses
            scan_list = ljm.namesToAddresses(len(scan_list), scan_list)[0]

            # --- Configuration ---
            # Ensure triggered stream is disabled.
            ljm.eWriteName(self.handle, "STREAM_TRIGGER_INDEX", 0)
            # Enabling internally-clocked stream.
            ljm.eWriteName(self.handle, "STREAM_CLOCK_SOURCE", 0)
            # Set resolution index.
            ljm.eWriteName(self.handle, "STREAM_RESOLUTION_INDEX", stream_resolution_index)
            # Set settling time.
            ljm.eWriteName(self.handle, "STREAM_SETTLING_US", settling_us)

            # --- Stream Start ---
            act_scan_rate = ljm.eStreamStart(self.handle, scans_per_read, len(scan_list), scan_list, scan_rate)
            print("\nStream started with a scan rate of %0.0f Hz." % act_scan_rate)

            if callback is not None:
                ljm.setStreamCallback(self.handle, callback, obj, workq)
        
        except:
            print("\033[91mError starting stream. Please check the LabJack connection and configuration.\033[0m")
            print(sys.exc_info()[1])
            exit(1)
        return act_scan_rate
    
    def read_stream_start_time(self):
        return ljm.eReadName(self.handle, "STREAM_START_TIME_STAMP")

    def read_stream(self):
        return ljm.eStreamRead(self.handle)
    
    def is_streaming(self):
        return ljm.eReadName(self.handle, "STREAM_ENABLE")

    def stop_stream(self):
        ljm.eStreamStop(self.handle)
        print(f"\nStream stopped at time: {time.time()}")
    
    def print_info(self):
        info = self.info
        # From https://github.com/labjack/labjack-ljm-python/blob/master/Examples/More/Stream/stream_callback.py
        print("Opened a LabJack with Device type: %i, Connection type: %i,\n"
          "Serial number: %i, IP address: %s, Port: %i,\nMax bytes per MB: %i" %
          (info[0], info[1], info[2], ljm.numberToIP(info[3]), info[4], info[5]))
    
    def print_info_pretty(self):
        print("———— LabJack Info ————")
        print(f"  Device Type : {self.get_device_type()}")
        print(f"  Serial Number: {self.get_serial_number()}")
        print(f"  Connection Type: {self.get_connection_type()}")
        if self.get_connection_type() == "ETHERNET" or self.get_connection_type() == "WIFI":
            print("  IP Address: " + self.get_ip_address())

    def get_device_type(self):
        if self.info[0] == ljm.constants.dtT8:
            return "T8"
        elif self.info[0] == ljm.constants.dtT7:
            return "T7"
        elif self.info[0] == ljm.constants.dtT4:
            return "T4"
        else:
            return f"{self.info[0]}"

    def get_serial_number(self):
        return self.info[2]
    
    def get_ip_address(self):
        return ljm.numberToIP(self.info[3])
    
    def get_connection_type(self):
        if self.info[1] == ljm.constants.ctUSB:
            return "USB"
        elif self.info[1] == ljm.constants.ctETHERNET:
            return "ETHERNET"
        elif self.info[1] == ljm.constants.ctWIFI:
            return "WIFI"
        else:
            return f"{self.info[1]}"
    
    def get_handle(self):
        return self.handle

class AnalogInput:
    def __init__(self, lj, channel_name, resolution_index):
        """
        Analog input channel for the LabJack T-Series
        @param lj : LabJack object
        @param channel_name : AIN channel name, e.g. "AIN0" (0-254, value not checked)
        @param resolution_index : Resolution index, 1-12 for T7-Pro
        """
        # Verify that the channel name is valid
        if not channel_name.startswith("AIN"):
            print("Invalid channel name. Please enter a valid AIN channel name.")
            raise ValueError("Invalid channel name")

        self.lj = lj
        self.channel_name = channel_name
        self.resolution_index = resolution_index

        self.set_resolution(resolution_index)
    
    def set_range(self, voltage_range):
        """
        Set the voltage range for the analog input channel.
        @param voltage_range: Voltage range, either 10, 1, 0.1, or 0.01 for T7-Pro
        """
        if voltage_range in [10, 1, 0.1, 0.01]:
            ljm.eWriteName(self.lj.handle, self.channel_name + "_RANGE", voltage_range)
        else:
            print("Invalid voltage range. Please enter one of the following: 10, 1, 0.1, 0.01")

    def set_resolution(self, resolution_index):
        """
        Set the resolution index for the analog input channel.
        @param resolution_index: Resolution index, 1-12 for T7-Pro
        """
        if resolution_index in range(1, 13):
            self.resolution_index = resolution_index
            ljm.eWriteName(self.lj.handle, self.channel_name + "_RESOLUTION_INDEX", self.resolution_index)
        else:
            print("Invalid resolution index. Please enter a number between 1 and 12.")

    def set_mode(self, mode, negative_channel = 199):
        """
        Set the mode of the analog input channel.
        @param mode: "SE" for single-ended, "DIFF" for differential
        @param negative_channel: The negative channel for differential mode
        """
        if mode == "DIFF":
            ljm.eWriteName(self.lj.handle, self.channel_name + "_NEGATIVE_CH", negative_channel)
        elif mode == "SE":
            ljm.eWriteName(self.lj.handle, self.channel_name + "_NEGATIVE_CH", 199)
        else:
            print("Invalid mode. Please enter either 'SE' or 'DIFF'.")

    def read(self):
        return ljm.eReadName(self.lj.handle, self.channel_name)

class AnalogOutput:
    def __init__(self, lj, channel_name):
        """
        Analog output channel for the LabJack
        @param lj : LabJack object
        @param channel_name : DAC channel name, either "DAC0"
        """
        if channel_name not in ["DAC0", "DAC1"]:
            print("Invalid channel name. Please enter either 'DAC0' or 'DAC1'.")
            raise ValueError("Invalid channel name")

        self.lj = lj
        self.channel_name = channel_name

    def write(self, volts : float):
        """
        Write a voltage to the DAC channel.
        @param volts: Output voltage, note: 0-5V for T4/7 and 0-10V for T7-Pro
        @note The DAC likely needs a calibration
        """
        if volts < 0 or volts > self.lj.dacMaxVolts:
            print(f"Invalid voltage. Please enter a voltage between 0 and {self.lj.dacMaxVolts}.")
            return False
        ljm.eWriteName(self.lj.handle, self.channel_name, volts)
        return True

class DigitalInput:
    def __init__(self, lj : LabJack, channel_name : str):
        """
        Digital input channel for the LabJack
        @param lj : LabJack object
        @param channel_name : DIO channel name, (includes FIO/EIO/CIO/MIO), e.g. "FIO0"
            value not checked
        """
        # Verify that the channel name is valid
        if channel_name[0:3] not in ["FIO", "EIO", "CIO", "MIO"]:
            print(f"Invalid channel name {channel_name}. Please enter a valid DIO channel name.")
            raise ValueError("Invalid channel name")

        self.lj = lj
        self.channel_name = channel_name

    def read(self):
        """
        Read the value of the digital input channel as 0 or 1.
        @return: 0 = low, 1 = high
        """
        return ljm.eReadName(self.lj.handle, self.channel_name)

class DigitalOutput:
    def __init__(self, lj : LabJack, channel_name : str):
        """
        Digital output channel for the LabJack
        @param lj : LabJack object
        @param channel_name : DIO channel name, (includes FIO/EIO/CIO/MIO), e.g. "FIO0"
            value not checked
        """
        # Verify that the channel name is valid
        if channel_name[0:3] not in ["FIO", "EIO", "CIO", "MIO"]:
            print(f"Invalid channel name {channel_name}. Please enter a valid DIO channel name.")
            raise ValueError("Invalid channel name")
        
        self.lj = lj
        self.channel_name = channel_name

    def write(self, value : int):
        """
        Write a value to the digital output channel.
        @param value: 0 = low, 1 = high
        """
        ljm.eWriteName(self.lj.handle, self.channel_name, value)
        
    def write(self, value : bool):
        """
        Write a value to the digital output channel.
        @param value: False = low, True = high
        """
        wVal = int(value)
        ljm.eWriteName(self.lj.handle, self.channel_name, wVal)
    
    def off(self):
        """
        Set to low (0) state.
        """
        ljm.eWriteName(self.lj.handle, self.channel_name, 0)

    def on(self):
        """
        Set to high (1) state.
        """
        ljm.eWriteName(self.lj.handle, self.channel_name, 1)

    def toggle(self):
        """
        Toggle the state of the digital output channel.
        TODO: Test this function on hardware
        """
        value = ljm.eReadName(self.lj.handle, self.channel_name)
        ljm.eWriteName(self.lj.handle, self.channel_name, 1 - value)
