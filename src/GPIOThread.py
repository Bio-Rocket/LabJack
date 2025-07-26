import multiprocessing as mp
import threading
import signal
import time

import RPi.GPIO as GPIO

from br_threading.WorkQCommands import WorkQCmnd, WorkQCmnd_e


def gpio_abort_thread(gpio_workq: mp.Queue,
                      state_workq: mp.Queue,
                      pin: int,
                      pull_up: bool = True,
                      bounce_ms: int = 30):

    signal.signal(signal.SIGINT, signal.SIG_IGN)

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP if pull_up else GPIO.PUD_DOWN)

    stop_evt = threading.Event()

    last_level = GPIO.input(pin)
    if last_level == GPIO.LOW:
        state_workq.put(WorkQCmnd(WorkQCmnd_e.RPI_HARDWARE_ABORT, None))
    else:
        state_workq.put(WorkQCmnd(WorkQCmnd_e.RPI_HARDWARE_ABORT_CLEAR, None))

    def _callback(channel):
        nonlocal last_level
        level = GPIO.input(channel)
        if level == last_level:
            return
        last_level = level

        if level == GPIO.LOW:  # falling
            state_workq.put(WorkQCmnd(WorkQCmnd_e.RPI_HARDWARE_ABORT, None))
        else:  # rising
            state_workq.put(WorkQCmnd(WorkQCmnd_e.RPI_HARDWARE_ABORT_CLEAR, None))

    GPIO.add_event_detect(pin, GPIO.BOTH, callback=_callback, bouncetime=bounce_ms)

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
        GPIO.remove_event_detect(pin)
        GPIO.cleanup(pin)
        print("RPI-GPIO - cleaned up")
