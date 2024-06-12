import gi

gi.require_version("Atspi", "2.0")
from gi.repository import Atspi
import json
import os
import logging
from typing import Literal, Optional
import sys  # isort:skip

sys.path.append(".")  # isort:skip
from shared.shared_types import A11yElement  # isort:skip
import shared.config as config  # isort:skip
import gi
from lib import Singleton, InterruptableThread, AtspiEvent
import time


# Talon cannot recieve socket messages from the screenreader server
# However, it needs to know
def send_talon_progress_signal():
    pass


def get_name_fallback(accessible) -> str | Literal["NULL"]:
    if not accessible:
        return "NULL"
    else:
        name = accessible.get_name()
        return name if name else "NULL"


class Desktop(Singleton):
    @staticmethod
    def getRoot(specific_app: Optional[str] = None):
        """Gets the root by either the active window or a specific app override"""
        desktop = Atspi.get_desktop(0)

        # atspi gobject introspection doesn't support iterators
        desktop_child_count = desktop.get_child_count()
        for i in range(desktop_child_count):
            app = desktop.get_child_at_index(i)

            window_count = app.get_child_count()
            for j in range(window_count):
                window = app.get_child_at_index(j)

                if not window:
                    continue

                # states = get_states(window)

                ACTIVE = window.get_state_set().contains(Atspi.StateType.ACTIVE)
                # Active should not be used for objects which have State::Focusable or State::Selectable:
                # Those objects should use State::Focused and State::Selected respectively.

                # FOCUSABLE = window.get_state_set().contains(Atspi.StateType.FOCUSED)
                # SELECTABLE = window.get_state_set().contains(Atspi.StateType.SELECTED)

                if ACTIVE:
                    # logging.debug(f"{app.get_name()} {states}")
                    return app, window

                if specific_app and specific_app == app.get_name():
                    return app, window

        # Not needed since we care about what event is emitting the signal not which one recieves the singal. It is ok
        # if it is none

        # else:
        #     logging.debug(
        #         f"No root window found among {[desktop.get_child_at_index(i).get_name() for i in range(desktop_child_count)]}"
        #     )

        return (None, None)


class A11yTree(Singleton):
    constructor_handle: Optional[InterruptableThread] = None

    element_mapper: Optional[dict[A11yElement, Atspi.Accessible]] = None

    @classmethod
    def get_elements(
        cls, parent_app: str, root, accumulator: dict[A11yElement : Atspi.Accessible]
    ) -> list[A11yElement]:
        """
        Recursive method for creating the a11y tree within the separate creator thread.
        In a thread so it doesn't block when the user switches the focused app
        """
        if not root or A11yTree.constructor_handle.interrupted():
            return accumulator

        try:
            for i in range(root.get_child_count()):
                accessible: Atspi.Accessible = root.get_child_at_index(i)
                if not accessible:
                    continue

                point = accessible.get_position(Atspi.CoordType.SCREEN)
                states = accessible.get_state_set()
                # https://docs.gtk.org/atspi2/enum.StateType.html
                visible = states.contains(Atspi.StateType.VISIBLE)
                sensitive = states.contains(Atspi.StateType.SENSITIVE)
                focusable = states.contains(Atspi.StateType.FOCUSABLE)
                showing = states.contains(Atspi.StateType.SHOWING)

                # According to atspi docs, we should only need to use focusable here.
                # However, many applications don't apply STATE_FOCUSABLE on elements that
                # should be focusable, so it is better to check both and be safe
                INTERACTABLE: bool
                # these apps actually implements atspi properly, while most other apps do not
                # TODO: add more apps / edge cases here
                match parent_app:
                    case "code":
                        INTERACTABLE = visible and showing and (focusable)
                    # Firefox doesn't always add focusable to certain dom elements that should be focusable so sensitive is used instead
                    case "firefox" | _:
                        INTERACTABLE = visible and showing and (focusable or sensitive)

                x = point.x
                y = point.y
                pid = accessible.get_process_id()
                role = accessible.get_role_name()
                name = accessible.get_name()
                element = A11yElement(name, x, y, role, pid)

                # OFF_SCREEN = x < -2000 or y < -2000

                UNLABELED = name == ""

                if element in accumulator:
                    logging.warning(
                        f"Element {element.to_dict()} was in the tree at least twice"
                    )

                if INTERACTABLE and not UNLABELED:  # and not OFF_SCREEN
                    accumulator[element] = accessible

                A11yTree.get_elements(parent_app, accessible, accumulator)
        except gi.repository.GLib.GError as ge:
            logging.error(
                f"Error while creating a11y tree for {parent_app} with root {get_name_fallback(root)}: {ge}"
            )

        return accumulator

    @classmethod
    def dump(cls, event: AtspiEvent):
        """Dump a serialized version of the a11y tree to the ipc file"""
        start = time.time()

        """
        At the time window:activate is output, the old_app is currently still focused. 
        So we need to look for the source of the window:activate event to find the new
        focused app
        """
        old_app, old_root = Desktop.getRoot()

        tree_action = "interrupting" if A11yTree.constructor_handle else "starting"
        logging.debug(
            f"Dump {tree_action} with {(event.type)} from {get_name_fallback(event.source)} inside {get_name_fallback(old_app)} with root: {get_name_fallback(old_root)}"
        )

        new_app_name = event.source.get_application().get_name()

        _, new_app_root = Desktop.getRoot(new_app_name)

        # remove all cached states to make sure we are getting the latest state for each element
        if new_app_root:
            new_app_root.clear_cache()
        if old_root:
            old_root.clear_cache()

        # Interrupt any existing tree dump if it is still running
        if A11yTree.constructor_handle:
            A11yTree.constructor_handle.interrupt()
            # Make the old thread finish before we spawn a new one
            A11yTree.constructor_handle.join()
            A11yTree.constructor_handle = None

        def interruptable_portion():
            """
            All operations in this function can be interrupted by the user to stop the tree dump
            This is done so if the user switches context many times, it doesn't cause the atspi
            server to block on many tree updates and slow down the UI with many updates all at once
            """
            elements = A11yTree.get_elements(new_app_name, new_app_root, accumulator={})

            assert elements is not None

            # Handle all cases where the dump completes yet should not be rendered
            if A11yTree.constructor_handle.interrupted():
                logging.debug(f"Tree dump interrupted for {new_app_name}")
                return
            elif event.source.get_role() == Atspi.Role.FRAME and len(elements) == 0:
                logging.debug(
                    f"Skipped tree dump for internal frame inside {new_app_name} with {len(elements)} elements"
                )
                return
            elif len(elements) == 0 and event.type == "object:state-changed:focused":
                logging.debug(
                    f"Skipped tree dump for pseudo update inside {new_app_name}."
                )
                return

            # Once the thread is done, get rid of the handle
            A11yTree.constructor_handle = None

            # Cache the elements in the mapper so the api server can get the a11y object
            A11yTree.element_mapper = elements

            if os.path.exists(config.TREE_OUTPUT_PATH):
                os.remove(config.TREE_OUTPUT_PATH)

            with open(config.TREE_OUTPUT_PATH, "w") as outfile:
                entire_tree_serialized = [
                    element.to_dict() for element in elements.keys()
                ]
                json.dump(entire_tree_serialized, outfile)

            delta = round(time.time() - start, 2)

            logging.debug(
                f"Dumped tree with {len(elements)} elements in {delta} seconds"
            )

        """
        We use a thread so if the user focused another window, we can immediately
        stop the tree dump and start a new one
        """
        A11yTree.constructor_handle = InterruptableThread(target=interruptable_portion)
        A11yTree.constructor_handle.start()

        # TODO remove this
        A11yTree.constructor_handle.join()
        """
        TODO:

        The underlying atspi c library crashes if queried too quickly with many shifts between apps
        with fast interrupts. join() is here to prevent interrupts and that should not crash. 
        TODO look into why libatspi crashes 
        
        All the Python logic is correct, not much that can be done without modifying the C library

        Error:
        gi.repository.GLib.GError: atspi_error: The process appears to be hung. (1)
        make: *** [makefile:7:  Segmentation fault (core dumped)
        """
