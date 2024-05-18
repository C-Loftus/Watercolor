import pyatspi.registry

from api_server import IPC_Server
import threading, os
import pyatspi
from create_coords import A11yTree
from lib import init_logger
import sys
sys.path.append(".")
import shared.config as config

def main():

    # Clean up old logs and ipc files
    for file in ["atspi_log.txt", config.TREE_OUTPUT_PATH,  config.SOCKET_PATH, "talon_server_error.log"]:
        if os.path.exists(file):
            os.unlink(file)

    init_logger()

    try:
        server = IPC_Server()
        server_thread = threading.Thread(target=server.listen)
        server_thread.start()


        for event in ["window:activate", "window:create", "window:deactivate", "window:destroy", "window:maximize", "window:minimize", "window:move", "focus", "object:visible-data-changed"]:
            pyatspi.Registry.registerEventListener(A11yTree.dump, event)

        pyatspi.Registry.start()        

    except KeyboardInterrupt:
        server.stop()
        
    
if __name__ == "__main__":
    main()