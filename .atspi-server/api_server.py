import json
import socket
import time
import traceback
from datetime import datetime
from typing import Optional
import pyatspi
# We need to add the root directory to the path for the shared module
import sys # isort:skip
sys.path.append(".") # # isort:skip
from shared import config
from shared.shared_types import WatercolorCommand, ServerStatusResult, ServerResponse, ClientPayload, A11yElement # isort:skip
from create_coords import A11yTree 
from lib import Singleton

def handle_command(command: ClientPayload) -> tuple[WatercolorCommand, ServerStatusResult]:
    command = command["command"]
    
    element = A11yElement.from_dict(command["target"])        
    atspi_element: pyatspi.Accessible = A11yTree.get_accessible_from_element(element)  
    invokable_actions = atspi_element.get_action_iface()
    print(invokable_actions)  

    return command, ServerStatusResult.SUCCESS


# Singleton class for handling IPC
class IPC_Server(Singleton):

    running = False
    server_socket: socket.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client_socket: Optional[socket.socket] = None

    # _client_lock = DebuggableLock("Client")
    # _server_lock = DebuggableLock("Server") 

    def __init__(self):
        raise TypeError("Instances of this class are not allowed")

    @classmethod
    def handle_client(cls):

        data = cls.client_socket.recv(1024)

        response_for_client: ServerResponse = {
            "command": None,
            "result": ServerStatusResult.RUNTIME_ERROR.value
        }

        try:
            client_request: ClientPayload = json.loads(data.decode().strip())
            command, result = handle_command(client_request)


            response_for_client: ServerResponse = {
            "command": command,
            "result": result.value
            }

        except json.JSONDecodeError as e:
            print(f"RECEIVED INVALID JSON FROM CLIENT: {e}")
            response_for_client: ServerResponse = {
            "result": ServerStatusResult.JSON_ENCODE_ERROR.value
            }

        finally:
            if cls.client_socket.fileno() != -1:
                cls.client_socket.sendall(json.dumps(response_for_client).encode("utf-8"))


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
                cls.stop()
                with open(
                    "talon_server_error.log",
                    "a",
                ) as f:
                    f.write(
                        f"\nERROR AT {datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')}: {e}"
                    )
                    f.write(f"\n{traceback.format_exc()}")
                    f.write(f"\nINTERNAL STATE: {cls.__dict__}\n")
                break
            finally:
                if cls.client_socket and cls.client_socket.fileno() != -1:
                    cls.client_socket.close()

    @classmethod
    def stop(cls):

        # Don't even try to hold the lock if everything has already been cleaned up from the other thread
        if not cls.running:
            if not cls.client_socket or cls.client_socket.fileno() == -1 and \
                not cls.server_socket or cls.server_socket.fileno() == -1:
                return

        if cls.client_socket and cls.client_socket.fileno() != -1:
            cls.client_socket.close()
        
        cls.running = False
        if cls.server_socket.fileno() != -1:
            cls.server_socket.close()

        print("TALON SERVER STOPPED")

