import pyatspi.registry

from api_server import IPC_Server
import threading, os
import pyatspi
from create_coords import A11yTree
from lib import init_logger, AtspiListenableEvent
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
        server_thread = threading.Thread(target=IPC_Server.listen)
        server_thread.start()

        # Don't watch window:deactivate since it will trigger after the activate and reset the hints
        event: AtspiListenableEvent
        for event in ["window:activate", "window:create", "window:destroy", "window:maximize", "window:minimize", "window:move", "focus", "object:visible-data-changed"]:
            pyatspi.Registry.registerEventListener(A11yTree.dump, event)

        pyatspi.Registry.start()        

    except KeyboardInterrupt:
        IPC_Server.stop()
        
    
if __name__ == "__main__":
    main()