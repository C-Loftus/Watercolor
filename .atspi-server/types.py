import enum
from multiprocessing import Lock
import contextlib
from typing import ContextManager, Generic, TypeVar

T = TypeVar("T")
class Mutex(Generic[T]):
  def __init__(self, value: T):
    self.__value = value
    self.__lock = Lock()

  @contextlib.contextmanager
  def lock(self) -> ContextManager[T]:
    self.__lock.acquire()
    try:
        yield self.__value
    finally:
        self.__lock.release()


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
