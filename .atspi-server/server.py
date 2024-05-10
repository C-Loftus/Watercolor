import enum
import json
import os
import socket
import time
import traceback
from datetime import datetime

SOCKET_PATH = "/tmp/watercolor-at-spi-server.sock"

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

valid_commands: list[str] = ["click"]


# Process a command, return the command and result as well as the retrieved value, if applicable
# Yes this is a big if/else block, but it's the most efficient way to handle the commands
def handle_command(command: str):
    pass


class IPC_Server:
    server_socket = None
    running = False
    client_socket = None

    def handle_client(self, client_socket: socket.socket):
        data = client_socket.recv(1024)

        response = ResponseSchema.generate()

        try:
            messages = json.loads(data.decode().strip())

            for message in messages:
                command, value, result = handle_command(message)
                response["processedCommands"].append(command)
                response["returnedValues"].append(value)
                # We can't pickle the StatusResult enum, so we have to convert it to a string
                response["statusResults"].append(result.value)

        except json.JSONDecodeError as e:
            print(f"RECEIVED INVALID JSON FROM TALON: {e}")
            response["statusResults"] = [StatusResult.JSON_ENCODE_ERROR.value]

        finally:
            client_socket.sendall(json.dumps(response).encode("utf-8"))

    def create_server(self):
        self.server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        
        try:
            self.server_socket.bind(SOCKET_PATH)
        except OSError as e:
            print(f"Failed to bind {SOCKET_PATH}: {e}")
            self.stop()
            return

        self.server_socket.listen(1)
        # Need a time short enough that we can reboot NVDA and the old socket will be closed and won't interfere
        self.server_socket.settimeout(0.5)
        print(f"TALON SERVER SERVING ON {self.server_socket.getsockname()}")

        self.running = True

        while self.running:
            try:
                # If it was closed from another thread, we want to break out of the loop
                if not self.server_socket:
                    break

                client_socket, _ = self.server_socket.accept()
                self.client_socket = client_socket
                self.client_socket.settimeout(0.3)
                self.handle_client(self.client_socket)
            # If the socket times out, we just want to keep looping
            except socket.timeout:
                pass
            except Exception as e:
                print(f"TALON SERVER CRASH: {e}")
                self.stop()
                with open(
                    "talon_server_error.log",
                    "a",
                ) as f:
                    f.write(
                        f"\nERROR AT {datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')}: {e}"
                    )
                    f.write(f"\n{traceback.format_exc()}")
                    f.write(f"\nINTERNAL STATE: {self.__dict__}\n")
                break
            finally:
                # Called no matter what even after a break
                if self.client_socket:
                    self.client_socket.close()

    def stop(self):
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        if self.client_socket:
            self.client_socket.close()
        if os.path.exists(SOCKET_PATH):
            os.remove(SOCKET_PATH)
        print("TALON SERVER STOPPED")

