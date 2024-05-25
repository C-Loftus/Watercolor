from api_server import IPC_Server
import threading
import os
import gi

gi.require_version("Atspi", "2.0")
from gi.repository import Atspi
from create_coords import A11yTree
from lib import init_logger, AtspiListenableEvent
import sys

sys.path.append(".")
import shared.config as config
import logging


def main():
    # Clean up old logs and ipc files
    for file in [
        "atspi_log.txt",
        config.TREE_OUTPUT_PATH,
        config.SOCKET_PATH,
        "talon_server_error.log",
    ]:
        if os.path.exists(file):
            os.unlink(file)

    init_logger()

    try:
        server_thread = threading.Thread(
            target=IPC_Server.listen,
        )
        server_thread.start()

        listeners = {}

        # Only register events that change the a11y tree
        # with visually relevant updates that change screen state
        relevant_events: list[AtspiListenableEvent] = [
            "window:activate",
            # Don't watch window:deactivate since it will trigger after the activate and reset the hints
            "window:create",
            "window:destroy",
            "window:maximize",
            "window:minimize",
            "window:move",
            # Can't use the object changed events since the tree sometimes does child changes
            # that don't actually affect the user interaction. Sometimes it outputs many changes and
            # triggers and infinite loop
            # "object:children-changed:add",
            # "object:children-changed:remove",
            "object:visible-data-changed",
            "object:row-reordered",
            "object:column-reordered",
            "object:state-changed:expanded",
            # "object:state-changed:focused",  # Used for firefox tab switching
            "document:page-changed",
            "document:load-complete",
            "document:page-changed",
            "document:attributes-changed",
            "document:reload",
        ]

        for event in relevant_events:
            listener: Atspi.EventListener = Atspi.EventListener.new(A11yTree.dump)
            listeners[listener] = event
            Atspi.EventListener.register(listener, event)

        match Atspi.init():
            case 0 as INITIALIZED:  # noqa: F841
                logging.info("Atspi initialized")
            case 1 as ALREADY_INITIALIZED:  # noqa: F841
                logging.debug(
                    "Atspi doesn't need to be initialized since it was already done"
                )
            case _ as e:
                msg = f"Error initializing Atspi with error code: {e}"
                logging.error(msg)
                raise RuntimeError(msg)

        interruptable_main = threading.Thread(target=Atspi.Event.main)
        interruptable_main.start()
        interruptable_main.join()

    except (RuntimeError, KeyboardInterrupt) as e:
        print(e)
        for listener in listeners:
            event = listeners[listener]
            Atspi.EventListener.deregister(listener, event)
        Atspi.Event.quit()

        IPC_Server.stop()


if __name__ == "__main__":
    main()
