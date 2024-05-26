from dataclasses import dataclass
import gi

gi.require_version("Atspi", "2.0")
from gi.repository import Atspi
from typing import Literal
import threading
import logging


class InterruptableThread(threading.Thread):
    def __init__(self, target=None, args=(), kwargs=None):
        super().__init__(
            target=target, args=args, kwargs=kwargs if kwargs is not None else {}
        )
        self._target = target
        self._args = args
        self._kwargs = kwargs if kwargs is not None else {}
        self._return_value = None
        self._stop_event = threading.Event()

    def run(self):
        if self._target:
            self._return_value = self._target(*self._args, **self._kwargs)

    # return the value of the thread when it is finished
    def join(self, *args, **kwargs):
        super().join(*args, **kwargs)
        return self._return_value

    def interrupt(self, log_message=""):
        if log_message:
            logging.debug(log_message)
        self._stop_event.set()

    def interrupted(self):
        return self._stop_event.is_set()


def get_states(accessible_obj):
    state_list = []
    for state in list(accessible_obj.get_state_set().get_states()):
        # atspi does not have a pretty print for enums so we do it manually
        state_str = str(state).split("enum ")[1].split("of type")[0].strip()

        state_list.append(state_str)

    return state_list


@dataclass
class AtspiEvent:
    """
    https://lazka.github.io/pgi-docs/Atspi-2.0/classes/Event.html
    """

    detail1: int
    detail2: int
    type: str
    sender: Atspi.Accessible
    source: Atspi.Accessible

    any_data: any


class Singleton:
    def __init__(self):
        raise TypeError(
            "This class represents a singleton and cannot be instantiated. Use only class methods"
        )


# We can't subclass the lock so we make it an attribute
class DebuggableLock:
    logger = logging.getLogger()

    def __init__(self, lock_name: str):
        self.lock = threading.Lock()
        self.name = lock_name

    def acquire(self, *args, **kwargs):
        holding_thread = threading.current_thread().name
        self.logger.lock_debug(
            f"Acquiring the {self.name} lock within thread: {holding_thread}."
        )

        self.lock.acquire(*args, **kwargs)

    def release(self, *args, **kwargs):
        holding_thread = threading.current_thread().name
        self.logger.lock_debug(
            f"Acquiring the {self.name} lock within thread: {holding_thread}."
        )

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

    logging.basicConfig(
        filename="atspi_log.txt",
        filemode="a",
        format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
        level=logging.DEBUG,
    )

    logging.info("Initializing Watercolor")


def inspect_element(accessible: Atspi.Accessible):
    stdout = ""

    point = accessible.get_position(Atspi.CoordType.SCREEN)
    x = point.x
    y = point.y
    states = get_states(accessible)
    parent_application = accessible.get_application().get_name()
    pid = accessible.get_process_id()
    role = accessible.get_role_name()
    name = accessible.get_name()
    stdout = f"{x=},{y=},{states=},{parent_application=},{pid=},{role=},{name=}"
    actions = accessible.get_action_iface()

    if not actions:
        return

    num_actions = actions.get_n_actions()
    if num_actions == 0:
        return
    for i in range(num_actions):
        description = actions.get_action_description(i)
        name = actions.get_action_name(i)
        stdout += f", Action {i}: {description=}, {name=}"

    # Print this serverside for logging reasons
    print(stdout)
    return stdout


AtspiListenableEvent = Literal[
    # https://docs.gtk.org/atspi2/method.EventListener.register.html
    "document:attributes-changed",
    "document:reload",
    "document:load-complete",
    "document:load-stopped",
    "document:page-changed",
    "mouse:button",
    "focus",
    "mouse:abs",
    "mouse:rel",
    "mouse:b1p",
    "mouse:b1r",
    "mouse:b2p",
    "mouse:b2r",
    "mouse:b3p",
    "mouse:b3r",
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
    "window:destroy",
]
