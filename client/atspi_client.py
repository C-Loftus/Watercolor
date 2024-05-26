import json
import enum
import socket
import threading
from typing import Literal, Optional, TypedDict, Union, assert_never, get_args
from ..shared.shared_types import ServerStatusResult, WatercolorCommand, ServerResponse
from ..shared import config

from talon import Module, app

mod = Module()
lock = threading.Lock()


class ClientResponse(enum.Enum):
    NO_RESPONSE = "noResponse"
    TIMED_OUT = "timedOut"
    GENERAL_ERROR = "generalError"
    SUCCESS = "success"


class ResponseBundle(TypedDict):
    client: ClientResponse
    # nullable if client fails before connecting to server
    server: Optional[ServerResponse]


def _notify_and_raise(msg: str):
    app.notify(msg)
    raise RuntimeError(msg)


def handle_ipc_result(
    client_response: ClientResponse,
    server_response: ServerResponse,
    command: WatercolorCommand,
):
    """
    Sanitize the response
    """

    match client_response:
        case (
            (
                ClientResponse.NO_RESPONSE
                | ClientResponse.TIMED_OUT
                | ClientResponse.GENERAL_ERROR,
                _,
            ) as communication_error
        ):
            _notify_and_raise(
                f"Could not connect to the atspi server due to {communication_error}"
            )
        case ClientResponse.SUCCESS:
            # empty case for pyright exhaustiveness
            pass
        case _:
            assert_never(client_response)

    cmd = server_response["command"]
    match server_response["result"]:
        case ServerStatusResult.SUCCESS:
            # empty case is here for exhaustiveness
            pass
        case ServerStatusResult.INVALID_COMMAND_ERROR:
            _notify_and_raise(f"Invalid command {cmd} sent to atspi server")
        case ServerStatusResult.JSON_ENCODE_ERROR:
            _notify_and_raise("Invalid JSON payload sent from client to atspi server")
        case (
            (
                ServerStatusResult.INTERNAL_SERVER_ERROR
                | ServerStatusResult.RUNTIME_ERROR
            ) as error
        ):
            _notify_and_raise(f"Server {error.value} processing command '{cmd}'")

        case ServerStatusResult.NO_ACTION_INTERFACE_ERROR:
            _notify_and_raise(
                "The targeted element is inaccessible and does not support running actions on it"
            )

        case ServerStatusResult.NO_ACTION_IMPLEMENTED_ERROR:
            _notify_and_raise(f"'{cmd}' not implemented by the targeted element")

        case None:
            _notify_and_raise(
                f"Server crashed or failed to return response for '{cmd}'"
            )
        case _:
            assert_never((server_response, command))


@mod.action_class
class ATSPIClientActions:
    def send_watercolor_command(
        payload: dict[str, str],
    ):
        """Sends a single command to the screenreader"""

        # We can only add client side verification for the command name, not the element
        if payload["command"] not in get_args(WatercolorCommand):
            raise ValueError(
                f"Caught invalid command '{payload['command']}' before sending to atspi server"
            )

        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(0.2)
        encoded = json.dumps(payload).encode()

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

                server_response: ServerResponse = json.loads(raw_data.decode("utf-8"))

                response["client"] = ClientResponse.SUCCESS

                response["server"] = {
                    "command": server_response["command"],
                    "result": ServerStatusResult.generate_from(
                        server_response["result"]
                    ),
                    "stdout": server_response["stdout"],
                }
                if server_response["stdout"]:
                    print(server_response["stdout"])

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

        handle_ipc_result(response["client"], response["server"], payload["command"])
