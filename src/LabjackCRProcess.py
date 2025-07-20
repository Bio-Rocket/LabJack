import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List
import multiprocessing as mp

from br_threading.WorkQCommands import WorkQCmnd, WorkQCmnd_e
from br_labjack.LabJackInterface import LabJack
from labjack.ljm import LJMError

CMD_RESPONSE_RATE_HZ = 5
CMD_RESPONSE_PERIOD = 1.0 / CMD_RESPONSE_RATE_HZ
AIN_LIST = [
    "AIN1", "AIN2", "AIN3", "AIN4", "AIN5", "AIN6", "AIN7",
    "AIN8", "AIN9", "AIN10", "AIN11", "AIN12", "AIN13"
]

@dataclass
class LjData():
    scan_rate: int
    lc_data: Dict[str, list]
    pt_data: Dict[str, list]

def connect_to_labjack():
    try:
        lji = LabJack("T7", "USB", "ANY")
    except LJMError as e:
        return False, None, str(e.errorString)
    return True, lji, ""

def t7_pro_cmd_response_thread(
    t7_pro_workq: mp.Queue,
    db_workq: mp.Queue,
    scan_frequency: int = CMD_RESPONSE_RATE_HZ,
    a_scan_list: List[str] = AIN_LIST):

    lji = None
    while lji is None:
        res, lji, err = connect_to_labjack()
        if not res:
            print(f"LJ - Error connecting to LabJack, {err}, retrying...")
            time.sleep(5)

    print("LJ - command-response thread started")

    pt_map = {
        "AIN1": "PT14", "AIN2": "PT13", "AIN3": "PT12", "AIN4": "PT11",
        "AIN5": "PT10", "AIN6": "PT9",  "AIN7": "PT8",  "AIN8": "PT7",
        "AIN9": "PT6"
    }
    lc_map = {
        "AIN10": "LC6", "AIN11": "LC5", "AIN12": "LC4", "AIN13": "LC3"
    }

    while True:
        start = time.time()

        try:
            values = lji.read_names(a_scan_list)
        except LJMError as e:
            print(f"LJ - Command/Response read error: {e}")
            continue

        pt_data = defaultdict(list)
        lc_data = defaultdict(list)

        for name, value in zip(a_scan_list, values):
            if name in pt_map:
                pt_data[pt_map[name]].append(value)
            elif name in lc_map:
                lc_data[lc_map[name]].append(value)

        cmnd = WorkQCmnd(WorkQCmnd_e.LJ_DATA, LjData(scan_frequency, lc_data, pt_data))
        db_workq.put(cmnd)

        try:
            if t7_pro_workq.get(timeout=0.01).command == WorkQCmnd_e.KILL_PROCESS:
                lji.stop_stream()
                lji.close()
                print("LJ - Command/Response thread stopped")
                return
        except:
            pass

        # CR rate
        elapsed = time.time() - start
        time.sleep(max(0, CMD_RESPONSE_PERIOD - elapsed))
