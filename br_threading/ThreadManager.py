# FILE: ThreadManager.py
# BRIEF: This file contains functionality that handles
#        the threads and inter-thread communication.

# General imports =================================================================================
import multiprocessing as mp
from dataclasses import dataclass

# Class Definitions ===============================================================================
class ThreadManager:
    thread_pool = []

    @staticmethod
    def start_threads():
        '''
        Start the threads in the thread pool
        '''
        for thread in ThreadManager.thread_pool:
            thread.start()
        return

    @staticmethod
    def create_thread(target, args):
        '''
        Create a thread and add it to the thread pool
        '''
        thread = mp.Process(target=target, args=args)
        ThreadManager.thread_pool.append(thread)
        return
