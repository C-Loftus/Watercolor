import enum
import threading
import inspect
import threading
import inspect
import logging
import os 


# We can't subclass the lock so we make it an attribute
class DebuggableLock:

    logger = logging.getLogger()
    def __init__(self):
        self.lock = threading.Lock()

    def acquire(self, *args, **kwargs):

        if os.getenv("DEBUG") == True:
            calling_function = inspect.stack()[1].function
            self.logger.lock_debug(f"Function '{calling_function}' is acquiring the lock.")

        self.lock.acquire(*args, **kwargs)

    def release(self, *args, **kwargs):


        if os.getenv("DEBUG") == True:
            calling_function = inspect.stack()[1].function
            self.logger.lock_debug(f"Function '{calling_function}' is acquiring the lock.")

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


