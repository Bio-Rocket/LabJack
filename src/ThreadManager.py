# FILE: ThreadManager.py
# BRIEF: This file contains functionality that handles
#        the threads and inter-thread communication.

# General imports =================================================================================
import multiprocessing as mp
from dataclasses import dataclass

from WorkQCmnd import WorkQCmnd, WorkQCmnd_e

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
                ThreadManager._get_workq(thread).put(WorkQCmnd(WorkQCmnd_e.KILL_PROCESS, None))
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
        pass