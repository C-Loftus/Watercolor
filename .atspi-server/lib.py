import enum
import threading
import inspect
import threading
import inspect
import logging
import os 

import threading

class StoppableThread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self,  *args, **kwargs):
        super(StoppableThread, self).__init__(*args, **kwargs)
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()



class Singleton:
    def __init__(self):
        raise TypeError("This class represents a singleton and cannot be instantiated. Use only class methods")

# We can't subclass the lock so we make it an attribute
class DebuggableLock:

    logger = logging.getLogger()
    def __init__(self, lock_name: str):
        self.lock = threading.Lock()
        self.name = lock_name

    def acquire(self, *args, **kwargs):

        holding_thread = threading.current_thread().name
        self.logger.lock_debug(f"Acquiring the {self.name} lock within thread: {holding_thread}.")

        self.lock.acquire(*args, **kwargs)

    def release(self, *args, **kwargs):


        holding_thread = threading.current_thread().name
        self.logger.lock_debug(f"Acquiring the {self.name} lock within thread: {holding_thread}.")

        self.lock.release(*args, **kwargs)

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.release()


def init_logger():
    # Define custom log level for lock operations
    LOCK_DEBUG_LEVEL = 25  # Custom log level number

    # Define the custom log level name and register it with the logging module
    logging.addLevelName(LOCK_DEBUG_LEVEL, "LOCK")

    # Define a custom log level function
    def lock_debug(self, message, *args, **kwargs):
        if self.isEnabledFor(LOCK_DEBUG_LEVEL):
            self._log(LOCK_DEBUG_LEVEL, message, args, **kwargs)


    # Add the custom log level function to the Logger class
    logging.Logger.lock_debug = lock_debug

    logging.basicConfig(filename="atspi_log.txt",
                            filemode='a',
                            format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                            datefmt='%H:%M:%S',
                            level=logging.INFO)

    logging.info("Initializing Watercolor")


