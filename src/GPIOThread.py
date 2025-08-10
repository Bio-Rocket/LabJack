import multiprocessing as mp
import threading
import signal
import atexit
import sys
import time
import RPi.GPIO as GPIO

from br_threading.WorkQCommands import WorkQCmnd, WorkQCmnd_e

def gpio_abort_thread(gpio_workq: mp.Queue,
                      state_workq: mp.Queue,
                      pin: int,
                      pull_up: bool = True,
                      bounce_ms: int = 30):

    stop_evt = threading.Event()

    def _handle_signal(_sig, _frm):
        stop_evt.set()
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)

    try:
        GPIO.cleanup(pin)
    except Exception:
        pass

    pud = GPIO.PUD_UP if pull_up else GPIO.PUD_DOWN

    for _ in range(5):
        try:
            GPIO.setup(pin, GPIO.IN, pull_up_down=pud)
            break
        except Exception as e:
            if "busy" in str(e).lower():
                time.sleep(0.1)
                continue
            raise
    else:
        raise RuntimeError(f"GPIO {pin} is busy. Use `gpioinfo`/`fuser -v /dev/gpiochip0` to find the holder.")

    last_level = GPIO.input(pin)

    state_workq.put(WorkQCmnd(
        WorkQCmnd_e.RPI_HARDWARE_ABORT if last_level == GPIO.LOW
        else WorkQCmnd_e.RPI_HARDWARE_ABORT_CLEAR,
        None
    ))

    def _callback(channel):
        nonlocal last_level
        level = GPIO.input(channel)
        if level == last_level:
            return
        last_level = level
        state_workq.put(WorkQCmnd(
            WorkQCmnd_e.RPI_HARDWARE_ABORT if level == GPIO.LOW
            else WorkQCmnd_e.RPI_HARDWARE_ABORT_CLEAR,
            None
        ))

    GPIO.add_event_detect(pin, GPIO.BOTH, callback=_callback, bouncetime=bounce_ms)

    def _cleanup():
        try: GPIO.remove_event_detect(pin)
        except Exception: pass
        try: GPIO.cleanup(pin)
        except Exception: pass
        print("RPI-GPIO - cleaned up")

    atexit.register(_cleanup)

    try:
        while not stop_evt.is_set():
            try:
                msg: WorkQCmnd = gpio_workq.get(timeout=0.25)
            except Exception:
                continue

            if msg.command == WorkQCmnd_e.KILL_PROCESS:
                print("RPI-GPIO - kill received")
                stop_evt.set()
    finally:
        _cleanup()
