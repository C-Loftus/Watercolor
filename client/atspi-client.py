import ipaddress
import json, enum
import os
import socket
import threading
from typing import Optional, Tuple, TypedDict, assert_never
from ..shared.types import WatercolorCommand, ServerStatusResult, ServerResponse
from ..shared import config

from talon import Context, Module, actions, cron, settings

mod = Module()
lock = threading.Lock()


class ClientResponse(enum.Enum):
    NO_RESPONSE = "noResponse"
    TIMED_OUT = "timedOut"
    GENERAL_ERROR = "generalError"
    SUCCESS = "success"


class ResponseBundle(TypedDict):
    client: ClientResponse
    server: ServerResponse

def handle_ipc_result(
    client_response: ClientResponse,
    server_response: ServerResponse,
):
    """
    Sanitize the response and return just the commands and their return values
    if present
    """

    match client_response:
        case (
            ClientResponse.NO_RESPONSE
            | ClientResponse.TIMED_OUT
            | ClientResponse.GENERAL_ERROR,
            _,
        ) as error:
            raise RuntimeError(
                f"Clientside {error=} communicating with screenreader extension"
            )
        case (ClientResponse.SUCCESS, _):
            # empty case for pyright exhaustiveness
            pass

    cmd = server_response["command"]
    match (server_response["result"]):

        case ServerStatusResult.SUCCESS:
            # empty case is here for exhaustiveness
            pass
        case ServerStatusResult.INVALID_COMMAND_ERROR:
            cmd = server_response["command"]
            raise ValueError(f"Invalid command '{cmd}' sent to screenreader")
        case ServerStatusResult.JSON_ENCODE_ERROR:
            raise ValueError(
                "Invalid JSON payload sent from client to screenreader"
            )
        case (
            ServerStatusResult.INTERNAL_SERVER_ERROR
            | ServerStatusResult.RUNTIME_ERROR
        ) as error:
            raise RuntimeError(f"{error} processing command '{cmd}'")
        case _:
            assert_never((server_response["result"], server_response["command"]))


@mod.action_class
class ATSPIClientActions:
    def send_ipc_command(
        command: WatercolorCommand,
    ) -> Optional[any]:
        """Sends a single command to the screenreader"""

        if not isinstance(command, WatercolorCommand):
            raise ValueError(f"Commmand '{command}' is not a valid command to send to the atspi server")

        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(0.2)
        encoded = json.dumps(command).encode()

        # Default response if nothing is set
        response: ResponseBundle = {
            "client": ClientResponse.NO_RESPONSE,
            "server": None,
        }

        # Although the screenreader server will block while processing commands,
        # having a lock client-side prevents errors when sending multiple commands
        with lock:
            try:
                sock.connect(config.SOCKET_PATH)
                sock.sendall(encoded)
                # Block until we receive a response
                # We don't want to execute further commands until we get a response
                raw_data = sock.recv(1024)

                raw_response: ServerResponse = json.loads(raw_data.decode("utf-8"))
                raw_response["statusResults"] = [
                    ServerStatusResult.generate_from(status)
                    for status in raw_response["statusResults"]
                ]
                response["client"] = ClientResponse.SUCCESS
                response["server"] = raw_response
            except KeyError as enum_decode_error:
                print("Error decoding enum", enum_decode_error, response)
                response["client"] = ClientResponse.GENERAL_ERROR
            except socket.timeout:
                response["client"] = ClientResponse.TIMED_OUT
            except Exception as fallback_error:
                response["client"] = ClientResponse.GENERAL_ERROR
                print(
                    fallback_error,
                    response,
                )
            finally:
                sock.close()

        handle_ipc_result(response["client"], response["server"])
