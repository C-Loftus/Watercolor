import dataclasses
import enum
from typing import TypedDict, Literal

class ServerStatusResult(enum.Enum):
    SUCCESS = "success"
    INTERNAL_SERVER_ERROR = "serverError"
    INVALID_COMMAND_ERROR = "commandError"
    RUNTIME_ERROR = "runtimeError"
    JSON_ENCODE_ERROR = "jsonEncodeError"
    NO_ACTION_SUPPORTED_ERROR = "noActionSupportedError"
    NO_ACTION_INTERFACE_ERROR = "noInterfaceError"

    @staticmethod
    def generate_from(value: str):
        for member in ServerStatusResult:
            if member.value == value:
                return member
        raise KeyError(f"Invalid status result: {value}")


WatercolorCommand = Literal["click", "inspect"]


class ServerResponse(TypedDict):
    command: WatercolorCommand
    result: ServerStatusResult


class ResponseBundle(TypedDict):
    client: ServerResponse
    server: ServerResponse

@dataclasses.dataclass(frozen=True)
class A11yElement():
    name: str
    x: int
    y: int
    role: str
    pid: int

    # nicer chainable representation
    def to_dict(self):
        return dataclasses.asdict(self)
    
    @classmethod
    def from_dict(cls, d):  
        return cls(**d)
    

class ClientPayload(TypedDict):
    command: WatercolorCommand
    # We are sending over the serialized dict not the dataclass itself
    target: dict[
        "name": str,
        "x": int,
        "y": int,
        "role": str,
        "pid": int
    ]