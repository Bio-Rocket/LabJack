import multiprocessing as mp
import threading, signal, atexit, sys, time, os
import RPi.GPIO as GPIO
from br_threading.WorkQCommands import WorkQCmnd, WorkQCmnd_e

def gpio_abort_thread(gpio_workq: mp.Queue,
                      state_workq: mp.Queue,
                      pin_bcm: int,             
                      pull_up: bool = True,
                      bounce_ms: int = 30):

    stop_evt = threading.Event()

    def _handle_signal(_sig, _frm):
        stop_evt.set()
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    try:
        GPIO.cleanup(pin_bcm)
    except:
        pass

    pud = GPIO.PUD_UP if pull_up else GPIO.PUD_DOWN
    GPIO.setup(pin_bcm, GPIO.IN, pull_up_down=pud)

    last_level = GPIO.input(pin_bcm)
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
        evt = (WorkQCmnd_e.RPI_HARDWARE_ABORT if level == GPIO.LOW
               else WorkQCmnd_e.RPI_HARDWARE_ABORT_CLEAR)
        print(f"[GPIO] Edge on BCM{channel}: level={level}")
        state_workq.put(WorkQCmnd(evt, None))

    GPIO.add_event_detect(pin_bcm, GPIO.BOTH, bouncetime=bounce_ms)
    GPIO.add_event_callback(pin_bcm, _callback)

    def _cleanup():
        try:
            GPIO.remove_event_detect(pin_bcm)
        except:
            pass
        try:
            GPIO.cleanup(pin_bcm)
        except:
            pass
        print("[GPIO] cleaned up")

    atexit.register(_cleanup)

    try:
        while not stop_evt.is_set():
            try:
                msg: WorkQCmnd = gpio_workq.get(timeout=0.25)
            except Exception:
                continue
            if msg.command == WorkQCmnd_e.KILL_PROCESS:
                print("[GPIO] kill received")
                stop_evt.set()
    finally:
        _cleanup()
