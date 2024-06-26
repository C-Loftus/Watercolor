import gi

gi.require_version("Atspi", "2.0")
from gi.repository import Atspi

import json
import socket
import time
import traceback
from datetime import datetime
from typing import Optional

# We need to add the root directory to the path for the shared module
import sys  # isort:skip

sys.path.append(".")  # isort:skip
from shared import config  # isort:skip
from shared.shared_types import (
    WatercolorCommand,
    ServerStatusResult,
    ServerResponse,
    ClientPayload,
    A11yElement,
)  # isort:skip
from create_coords import A11yTree
from lib import Singleton, inspect_element
import logging


def handle_command(
    payload: ClientPayload,
) -> tuple[WatercolorCommand, ServerStatusResult, str]:
    logging.debug(f"Recieved {payload}")
    print(f"Recieved {payload}")
    command = payload["command"]
    stdout: str = ""

    element = A11yElement.from_dict(payload["target"])

    if not element:
        logging.error(
            f"Tried to click an element: {element}, but it doesn't exist in the tree"
        )
        return command, ServerStatusResult.INTERNAL_SERVER_ERROR, stdout

    if not A11yTree.element_mapper:
        logging.error(
            "Tried to get an a11y element but the mapper is not yet initialized"
        )
        return command, ServerStatusResult.INTERNAL_SERVER_ERROR, stdout

    atspi_element: Atspi.Accessible = A11yTree.element_mapper.get(element, None)

    if not atspi_element:
        print(f"Tried to click an element: {element}, but it doesn't exist in the tree")
        return command, ServerStatusResult.INTERNAL_SERVER_ERROR, stdout

    match command:
        case "click":
            actions = atspi_element.get_action_iface()

            if not actions:
                print(
                    f"No action interface found for element {atspi_element.get_name()}, with role: {atspi_element.get_role_name()}"
                )
                return command, ServerStatusResult.NO_ACTION_INTERFACE_ERROR, stdout

            num_actions = actions.get_n_actions()

            if num_actions == 0:
                print(
                    f"No actions found within {[actions.get_action_name(i) for i in range(num_actions)]}"
                )
                return command, ServerStatusResult.NO_ACTION_IMPLEMENTED_ERROR, stdout

            for i in range(num_actions):
                description = actions.get_action_description(i)
                name = actions.get_action_name(i)
                print(f"Action {i}: {description=}, {name=}")

            print(
                f"Running primary action {actions.get_action_name(0)} with description {actions.get_action_description(0)}"
            )
            actions.do_action(PRIMARY_ACTION := 0)  # noqa: F841

        case "inspect":
            stdout = inspect_element(atspi_element)

    return command, ServerStatusResult.SUCCESS, stdout


class IPC_Server(Singleton):
    running = False
    server_socket: socket.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client_socket: Optional[socket.socket] = None

    @classmethod
    def handle_client(cls):
        data = cls.client_socket.recv(1024)

        response_for_client: ServerResponse = {
            "command": None,
            "result": ServerStatusResult.RUNTIME_ERROR.value,
            "stdout": "",
        }

        try:
            client_request: ClientPayload = json.loads(data.decode().strip())
            command, result, stdout = handle_command(client_request)
            response_for_client: ServerResponse = {
                "command": command,
                "result": result.value,
                "stdout": stdout,
            }

        except json.JSONDecodeError as e:
            print(f"RECEIVED INVALID JSON FROM CLIENT: {e}")
            response_for_client["result"] = ServerStatusResult.JSON_ENCODE_ERROR.value

        finally:
            if cls.client_socket.fileno() != -1:
                cls.client_socket.sendall(
                    json.dumps(response_for_client).encode("utf-8")
                )

    @classmethod
    def listen(cls):
        try:
            cls.server_socket.bind(config.SOCKET_PATH)
        except OSError as e:
            print(f"Failed to bind to {config.SOCKET_PATH}: {e}")
            cls.stop()
            return

        cls.server_socket.listen(1)
        # Need a time short enough that we can reboot NVDA and the old socket will be closed and won't interfere
        cls.server_socket.settimeout(0.5)
        print(f"TALON SERVER SERVING ON {cls.server_socket.getsockname()}")

        cls.running = True

        while cls.running:
            try:
                # make this atomic so we exit if there is an update after checking
                if cls.server_socket and cls.server_socket.fileno() != -1:
                    try:
                        tmp_socket, _ = cls.server_socket.accept()
                    # catch when we close the server from the other thread, but still have this open socket in another thread
                    except OSError:
                        continue

                    cls.client_socket = tmp_socket
                    cls.client_socket.settimeout(0.3)

                    if not cls.running:
                        break

                    cls.handle_client()

            # If the socket times out, we just want to keep looping
            except socket.timeout:
                pass
            except Exception as e:
                print(f"TALON SERVER CRASH: {e}")
                logging.fatal(f"TALON SERVER CRASH: {e}")
                cls.stop()
                with open(
                    "talon_server_error.log",
                    "a",
                ) as f:
                    msgs = [
                        f"\nERROR AT {datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')}: {e}",
                        f"\n{traceback.format_exc()}",
                        f"\nINTERNAL STATE: {cls.__dict__}\n",
                    ]
                    for msg in msgs:
                        f.write(msg)
                        logging.fatal(msg)
                break
            finally:
                if cls.client_socket and cls.client_socket.fileno() != -1:
                    cls.client_socket.close()

    @classmethod
    def stop(cls):
        # Don't even try to hold the lock if everything has already been cleaned up from the other thread
        if not cls.running:
            if (
                not cls.client_socket
                or cls.client_socket.fileno() == -1
                and not cls.server_socket
                or cls.server_socket.fileno() == -1
            ):
                return

        if cls.client_socket and cls.client_socket.fileno() != -1:
            cls.client_socket.close()

        cls.running = False
        if cls.server_socket.fileno() != -1:
            cls.server_socket.close()

        print("TALON SERVER STOPPED")
