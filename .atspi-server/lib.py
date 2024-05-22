import threading
import threading
import logging
from dataclasses import dataclass
import pyatspi
from typing import Literal

import threading

class InterruptableThread(threading.Thread):

    def __init__(self,  *args, **kwargs):
        super(InterruptableThread, self).__init__(*args, **kwargs)
        self._stop_event = threading.Event()
        self._return = None

    def interrupt(self, log_message=""):
        if log_message:
            logging.debug(log_message)
        self._stop_event.set()

    def interrupted(self):
        return self._stop_event.is_set()
    
    def join(self, *args):
        threading.Thread.join(self, *args)
        return self._return


def get_states(accessible_obj):

    state_list = []
    for state in list(accessible_obj.get_state_set().get_states()):
        # atspi does not have a pretty print for enums so we do it manually
        state_str = str(state).split("enum ")[1].split("of type")[0]

        state_list.append(state_str)

    return state_list


@dataclass
class AtspiEvent():
    """
    https://lazka.github.io/pgi-docs/Atspi-2.0/classes/Event.html
    """
    detail1: int
    detail2: int
    type: pyatspi.appevent.EventType
    sender: pyatspi.Accessible
    source: pyatspi.Accessible

    any_data: any

class Singleton:
    def __init__(self):
        raise TypeError("This class represents a singleton and cannot be instantiated. Use only class methods")

# We can't subclass the lock so we make it an attribute
class DebuggableLock:

    logger = logging.getLogger()
    def __init__(self, lock_name: str):
        self.lock = threading.Lock()
        self.name = lock_name

    def acquire(self, *args, **kwargs):

        holding_thread = threading.current_thread().name
        self.logger.lock_debug(f"Acquiring the {self.name} lock within thread: {holding_thread}.")

        self.lock.acquire(*args, **kwargs)

    def release(self, *args, **kwargs):


        holding_thread = threading.current_thread().name
        self.logger.lock_debug(f"Acquiring the {self.name} lock within thread: {holding_thread}.")

        self.lock.release(*args, **kwargs)

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.release()


def init_logger():
    # Define custom log level for lock operations
    LOCK_DEBUG_LEVEL = 25  # Custom log level number

    # Define the custom log level name and register it with the logging module
    logging.addLevelName(LOCK_DEBUG_LEVEL, "LOCK")

    # Define a custom log level function
    def lock_debug(self, message, *args, **kwargs):
        if self.isEnabledFor(LOCK_DEBUG_LEVEL):
            self._log(LOCK_DEBUG_LEVEL, message, args, **kwargs)


    # Add the custom log level function to the Logger class
    logging.Logger.lock_debug = lock_debug

    logging.basicConfig(filename="atspi_log.txt",
                            filemode='a',
                            format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                            datefmt='%H:%M:%S',
                            level=logging.DEBUG)

    logging.info("Initializing Watercolor")

def inspect_element(accessible: pyatspi.Accessible):
    point = accessible.get_position(pyatspi.XY_SCREEN)
    x = point.x
    y = point.y
    states = get_states(accessible)
    parent_application = accessible.get_application().get_name()
    pid = accessible.get_process_id()
    role = accessible.get_role_name()
    name = accessible.get_name() 
    print(f"{x=}{y=}{states=}{parent_application=}{pid=}{role=}{name=}")

AtspiListenableEvent = Literal[
    # https://docs.gtk.org/atspi2/method.EventListener.register.html
    "document:attributes-changed",
    "document:reload",
    "document:load-complete",
    "document:load-stopped",
    "document:page-changed",
    "mouse:button",
    "object:announcement",
    "object:active-descendant-changed",
    "object:attributes-changed",
    "object:children-changed:add",
    "object:children-changed:remove",
    "object:column-reordered",
    "object:property-change:accessible-description",
    "object:property-change:accessible-name",
    "object:property-change:accessible-value",
    "object:row-reordered",
    "object:selection-changed",
    "object:state-changed:active",
    "object:state-changed:busy",
    "object:state-changed:checked",
    "object:state-changed:expanded",
    "object:state-changed:focused",
    "object:state-changed:indeterminate",
    "object:state-changed:pressed",
    "object:state-changed:selected",
    "object:state-changed:sensitive",
    "object:state-changed:showing",
    "object:text-attributes-changed",
    "object:text-caret-moved",
    "object:text-changed:delete",
    "object:text-changed:insert",
    "object:text-selection-changed",
    "object:value-changed",
    "window:activate",
    "window:create",
    "window:deactivate",
    "window:destroy"
]