import json
import socket
import time
import traceback
from datetime import datetime
from typing import Optional
from lib import DebuggableLock
import sys
sys.path.append(".") # So we can import shared outside of the package
from shared import config
from shared.shared_types import WatercolorCommand, ServerStatusResult, ServerResponse

def handle_command(command: WatercolorCommand):
    print(f"RECEIVED COMMAND: {command}")

# Singleton class for handling IPC
class IPC_Server:

    running = False
    server_socket: socket.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client_socket: Optional[socket.socket] = None
    _client_lock = DebuggableLock()
    _server_lock = DebuggableLock() 


    @classmethod
    def handle_client(cls):
        with cls._client_lock:

            data = cls.client_socket.recv(1024)

            response_for_client: ServerResponse = {
                "command": None,
                "result": ServerStatusResult.RUNTIME_ERROR.value
            }

            try:
                client_request = json.loads(data.decode().strip())
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
                cls._server_lock.acquire()
                if cls.server_socket and cls.server_socket.fileno() != -1:
                    tmp_socket, _ = cls.server_socket.accept()
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
                cls._server_lock.release()
                with cls._client_lock:
                    if cls.client_socket and cls.client_socket.fileno() != -1:
                        cls.client_socket.close()

    @classmethod
    def stop(cls):

        # Don't even try to hold the lock if everything has already been cleaned up from the other thread
        if not cls.running:
            if not cls.client_socket and cls.client_socket.fileno() == -1 and \
                not cls.server_socket and cls.server_socket.fileno() == -1:
                return

        print("Waiting for client to shut down")
        with cls._client_lock:
            print("Shutting down client")
            if cls.client_socket and cls.client_socket.fileno() != -1:
                cls.client_socket.close()
        
        print("Waiting for server to shut down")
        with cls._server_lock:
            print("Shutting down server")
            cls.running = False
            if cls.server_socket.fileno() != -1:
                cls.server_socket.close()

        print("TALON SERVER STOPPED")

