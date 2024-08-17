# FILE: ThreadManager.py
# BRIEF: This file contains functionality that handles
#        the threads and inter-thread communication.

# General imports =================================================================================
import multiprocessing as mp
from dataclasses import dataclass

# Project specific imports ========================================================================
from src.support.CommonLogger import logger

# Constants ========================================================================================
THREAD_MESSAGE_KILL = 'stop'
THREAD_MESSAGE_DB_WRITE = 'db_write'
THREAD_MESSAGE_SERIAL_WRITE = 'serial_write'
THREAD_MESSAGE_DB_COMMAND_NOTIF = 'db_command_notif'
THREAD_MESSAGE_DB_BACKEND_NOTIF = 'db_backend_notif'
THREAD_MESSAGE_HEARTBEAT = 'heartbeat'
THREAD_MESSAGE_HEARTBEAT_SERIAL = 'heartbeat_serial'
THREAD_MESSAGE_LOAD_CELL_VOLTAGE = 'loadcell_voltage'
THREAD_MESSAGE_LOAD_CELL_COMMAND = 'loadcell_command'
THREAD_MESSAGE_STORE_LOAD_CELL_SLOPE = 'store_load_cell_slope'
THREAD_MESSAGE_REQUEST_LOAD_CELL_SLOPE = 'get_last_loadcell_slope'
THREAD_MESSAGE_LOAD_CELL_SLOPE = 'loadcell_slope'


# Data Classes =====================================================================================
@dataclass
class WorkQ_Message:
    src_thread: str
    dest_thread: str
    message_type: str
    message: tuple

# Class Definitions ===============================================================================
class ThreadManager:
    def __init__(self) -> None:
        ThreadManager.thread_pool = dict()

    @staticmethod
    def start_threads():
        '''
        Start the threads in the thread pool
        '''
        for thread in ThreadManager.thread_pool:
            if ThreadManager.thread_pool[thread]['thread']:
                ThreadManager.thread_pool[thread]['thread'].start()
        return

    @staticmethod
    def kill_threads():
        '''
        Kill the threads in the thread pool
        '''
        for thread in ThreadManager.thread_pool:
            if ThreadManager.thread_pool[thread]['thread']:
                ThreadManager._get_workq(thread).put(WorkQ_Message("all", "main", THREAD_MESSAGE_KILL, None))
                ThreadManager._get_thread(thread).join()

    @staticmethod
    def _get_workq(thread_name) -> mp.Queue:
        '''
        Get the work queue for the specified thread
        '''
        return ThreadManager.thread_pool[thread_name]['workq']

    @staticmethod
    def _get_thread(thread_name) -> mp.Process:
        '''
        Get the work queue for the specified thread
        '''
        return ThreadManager.thread_pool[thread_name]['thread']

    @staticmethod
    def handle_thread_messages():
        '''
        Handle the messages in the thread work queues
        '''
        message_workq = ThreadManager.thread_pool['message_handler']['workq']
        
        message = message_workq.get(block=True)

        logger.debug(f"Handling thread messages from {message.src_thread} to {message.dest_thread} with message type: {message.message_type}")

        if message.dest_thread == "all_serial":
            for serial_thread in ['uart', 'radio']:
                if ((serial_thread not in ThreadManager.thread_pool) or
                    (not ThreadManager.thread_pool[serial_thread]['thread'].is_alive())):
                    logger.error(f"Attempting to send message to non-existent thread: {serial_thread}")
                    continue
                ThreadManager.thread_pool[serial_thread]['workq'].put(message)
        else:
            if ((message.dest_thread not in ThreadManager.thread_pool) or 
                (not ThreadManager.thread_pool[message.dest_thread]['thread'].is_alive())):
                logger.error(f"Attempting to send message to non-existent thread: {message.dest_thread}")
                return
            dest_workq = ThreadManager.thread_pool[message.dest_thread]['workq']
            if dest_workq:
                dest_workq.put(message)