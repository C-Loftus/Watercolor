import json
import os
import socket
import time
import traceback
from datetime import datetime
from typing import Optional
from custom_types import ResponseSchema, StatusResult, ValidCommands
import multiprocessing

SOCKET_PATH = "/tmp/watercolor-at-spi-server.sock"

def handle_command(command: ValidCommands):
    print(f"RECEIVED COMMAND: {command}")

# Singleton class for handling IPC
class IPC_Server:

    running = False
    server_socket: socket.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client_socket: Optional[socket.socket] = None
    _client_lock = multiprocessing.Lock() 
    _server_lock = multiprocessing.Lock() 


    @classmethod
    def handle_client(cls):
            
        with cls._client_lock:

            data = cls.client_socket.recv(1024)

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
                if cls.client_socket.fileno() != -1:
                    cls.client_socket.sendall(json.dumps(response).encode("utf-8"))


    @classmethod
    def listen(cls):
        
        try:
            cls.server_socket.bind(SOCKET_PATH)
        except OSError as e:
            print(f"Failed to bind to {SOCKET_PATH}: {e}")
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
                with cls._server_lock:
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
                with cls._client_lock:
                    if cls.client_socket and cls.client_socket.fileno() != -1:
                        cls.client_socket.close()

    @classmethod
    def stop(cls):

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
