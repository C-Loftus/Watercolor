import enum
import threading
import inspect
import threading
import inspect
import logging
import os 

logger = logging.getLogger()

# We can't subclass the lock so we make it an attribute
class DebuggableLock:
    def __init__(self):
        self.lock = threading.Lock()

    def acquire(self, *args, **kwargs):

        if os.getenv("DEBUG") == True:
            calling_function = inspect.stack()[1].function
            logger.lock_debug(f"Function '{calling_function}' is acquiring the lock.")

        self.lock.acquire(*args, **kwargs)

    def release(self, *args, **kwargs):


        if os.getenv("DEBUG") == True:
            calling_function = inspect.stack()[1].function
            logger.lock_debug(f"Function '{calling_function}' is acquiring the lock.")

        self.lock.release(*args, **kwargs)

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.release()


class ResponseSchema:
    def __init__(self):
        self.processedCommands = []
        self.returnedValues = []
        self.statusResults = []

    def generate():
        return {"processedCommands": [], "returnedValues": [], "statusResults": []}


class StatusResult(enum.Enum):
    SUCCESS = "success"
    INTERNAL_SERVER_ERROR = "serverError"
    INVALID_COMMAND_ERROR = "commandError"
    RUNTIME_ERROR = "runtimeError"
    JSON_ENCODE_ERROR = "jsonEncodeError"


class ValidCommands(enum.Enum):
    FOCUS = "focus"
    CLICK = "click"