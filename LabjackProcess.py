from typing import Any, List
from br_threading.WorkQCommands import WorkQCmnd, WorkQCmnd_e
from labjack.ljm import ljm
import multiprocessing as mp
from br_labjack.LabJackInterface import LabJack

LAB_JACK_SCAN_RATE = 4 # Scan rate in Hz

class _CallbackClass:
    def __init__(self, lji: LabJack, workq_list: List[mp.Queue]):
        """
        The callback class for the LabJack T7 Pro,
        including the labjack object to read from the stream and
        the list of threads that are subscribed to the labjack data.

        Args:
            lji (LabJack):
                The labjack object to read from the stream
            workq_list (List[mp.Queue]):
                The list of threads that are subscribed to the labjack data
        """
        self.lji = lji
        self.subscribed_workq_list = workq_list

def t7_pro_callback(obj: _CallbackClass, stream_handle: Any):
    """
    The callback function for the LabJack T7 Pro,
    for when the LabJack T7 Pro receives stream data.

    Args:
        obj (_CallbackClass): The callback class for the LabJack T7 Pro.
        stream_handle (Any): The stream handle for the LabJack T7 Pro.
    """
    ff = obj.lji.read_stream()
    cmnd = WorkQCmnd(WorkQCmnd_e.LJ_DATA, ff)

    for workq in obj.subscribed_workq_list:
        workq.put(cmnd)

def t7_pro_thread(t7_pro_workq: mp.Queue, db_workq: mp.Queue):
    """
    Start the LabJack stream to stream sensor data to
    the database thread.

    Args:
        t7_pro_workq (mp.Queue):
            The work queue for the LabJack T7 Pro thread. Used
            for changing valve positions and other commands.
        db_workq (mp.Queue):
            The work queue for the database thread. Used for
            storing sensor data in the database.
    """

    a_scan_list_names = ["AIN0",]
    scan_rate = LAB_JACK_SCAN_RATE
    stream_resolution_index = 0
    # a_scan_list = ljm.namesToAddresses(len(a_scan_list_names), a_scan_list_names)[0]

    lji = LabJack("ANY", "USB", "ANY")

    obj = _CallbackClass(lji, [db_workq,])

    lji.start_stream(a_scan_list_names, scan_rate, scans_per_read=1, callback=t7_pro_callback, obj = obj, stream_resolution_index= stream_resolution_index)

    while 1:
        t7_pro_workq.get(block=True)
