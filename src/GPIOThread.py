import multiprocessing as mp
import threading, signal, atexit, sys, time, os
import RPi.GPIO as GPIO
from br_threading.WorkQCommands import WorkQCmnd, WorkQCmnd_e

def gpio_abort_thread(gpio_workq: mp.Queue,
                      state_workq: mp.Queue,
                      pin_bcm: int,
                      pull_up: bool = True,
                      debounce_ms: int = 30,
                      poll_hz: float = 5):

    stop_evt = threading.Event()
    def _handle(_s, _f): stop_evt.set()
    signal.signal(signal.SIGINT, _handle)
    signal.signal(signal.SIGTERM, _handle)

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    try: GPIO.cleanup(pin_bcm)
    except Exception: pass

    pud = GPIO.PUD_UP if pull_up else GPIO.PUD_DOWN
    GPIO.setup(pin_bcm, GPIO.IN, pull_up_down=pud)

    last_raw = GPIO.input(pin_bcm)
    stable_level = last_raw
    state_workq.put(WorkQCmnd(
        WorkQCmnd_e.RPI_HARDWARE_ABORT if stable_level == GPIO.LOW
        else WorkQCmnd_e.RPI_HARDWARE_ABORT_CLEAR,
        None
    ))

    debounce_ns = int(debounce_ms * 1e6)
    stable_since = time.monotonic_ns()
    interval_ns = int((1.0 / poll_hz) * 1e9)
    next_t = time.monotonic_ns() + interval_ns

    def _publish(level: int):
        evt = (WorkQCmnd_e.RPI_HARDWARE_ABORT if level == GPIO.LOW
               else WorkQCmnd_e.RPI_HARDWARE_ABORT_CLEAR)
        state_workq.put(WorkQCmnd(evt, None))

    def _cleanup():
        try: GPIO.cleanup(pin_bcm)
        except Exception: pass

    atexit.register(_cleanup)

    try:
        while not stop_evt.is_set():
            # Handle control messages without blocking
            try:
                msg: WorkQCmnd = gpio_workq.get_nowait()
                if msg.command == WorkQCmnd_e.KILL_PROCESS:
                    stop_evt.set()
            except Exception:
                pass

            # Poll
            now = time.monotonic_ns()
            if now >= next_t:
                raw = GPIO.input(pin_bcm)
                if raw != last_raw:
                    last_raw = raw
                    stable_since = now  # start debounce timer
                else:
                    # if stable long enough & different from published state -> publish
                    if raw != stable_level and (now - stable_since) >= debounce_ns:
                        stable_level = raw
                        _publish(stable_level)
                next_t += interval_ns
                if now > next_t + interval_ns:
                    next_t = now + interval_ns
            else:
                time.sleep(0.1)
    finally:
        _cleanup()
