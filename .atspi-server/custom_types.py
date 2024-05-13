import enum
from multiprocessing import Lock

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