import pyatspi.registry
from server import IPC_Server
import threading, os
import pyatspi
from create_coords import A11yTree

def main():
    for file in ["atspi_log.txt", "/tmp/a11y_tree.json", "/tmp/watercolor-at-spi-server.sock"]:
        if os.path.exists(file):
            os.unlink(file)

    try:
        server = IPC_Server()
        server_thread = threading.Thread(target=server.create_server)
        server_thread.start()


        for event in ["window:activate", "window:create", "window:deactivate", "window:destroy", "window:maximize", "window:minimize", "window:move", "focus", "object:visible-data-changed"]:
            pyatspi.Registry.registerEventListener(A11yTree.dump, event)

        pyatspi.Registry.start()        

    except KeyboardInterrupt:
        server.stop()
        
    
if __name__ == "__main__":
    main()