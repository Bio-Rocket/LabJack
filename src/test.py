from modified_ljm import ljm
from LabJackInterface import LabJack

def t8_callback(lji, handle):
    ff = lji.read_stream()
    print(ff)

def test_stream():
    a_scan_list_names = ["AIN0"] 
    scan_rate = 2  # Scan rate in Hz
    stream_resolution_index = 0 
    a_scan_list = ljm.namesToAddresses(len(a_scan_list_names), a_scan_list_names)[0]

    lji = LabJack("ANY", "ANY", "ANY")
    lji.start_stream(a_scan_list_names, scan_rate, scans_per_read=None, callback=t8_callback, obj = lji, stream_resolution_index= stream_resolution_index)

test_stream()