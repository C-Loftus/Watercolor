import enum
from typing import TypedDict, Literal

class ServerStatusResult(enum.Enum):
    SUCCESS = "success"
    INTERNAL_SERVER_ERROR = "serverError"
    INVALID_COMMAND_ERROR = "commandError"
    RUNTIME_ERROR = "runtimeError"
    JSON_ENCODE_ERROR = "jsonEncodeError"

    @staticmethod
    def generate_from(value: str):
        for member in ServerStatusResult:
            if member.value == value:
                return member
        raise KeyError(f"Invalid status result: {value}")


WatercolorCommand = Literal["click", "focus"]


class ServerResponse(TypedDict):
    command: WatercolorCommand
    result: ServerStatusResult


class ResponseBundle(TypedDict):
    client: ServerResponse
    server: ServerResponse
