import dataclasses
import enum
from typing import TypedDict, Literal


class ServerStatusResult(enum.Enum):
    # Key values are all private and only used for
    # the serialized representations and regenerating
    # the enum over the wire

    SUCCESS = "success"
    INTERNAL_SERVER_ERROR = "serverError"
    INVALID_COMMAND_ERROR = "commandError"
    RUNTIME_ERROR = "runtimeError"
    JSON_ENCODE_ERROR = "jsonEncodeError"
    NO_ACTION_IMPLEMENTED_ERROR = "noActionImplementedError"
    NO_ACTION_INTERFACE_ERROR = "noActionInterfaceError"

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


class SerializedA11yElement(TypedDict):
    name: str
    x: int
    y: int
    role: str
    pid: int


@dataclasses.dataclass(frozen=True)
class A11yElement:
    name: str
    x: int
    y: int
    role: str
    pid: int

    # nicer chainable representation
    def to_dict(self) -> SerializedA11yElement:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, d: SerializedA11yElement):
        return cls(**d)


class ClientPayload(TypedDict):
    command: WatercolorCommand
    # We are sending over the serialized dict not the dataclass itself
    target: SerializedA11yElement
