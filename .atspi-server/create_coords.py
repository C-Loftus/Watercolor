import gi.repository
import pyatspi
import json
import os
import logging
from typing import ClassVar, Optional
import sys  # isort:skip

sys.path.append(".")  # isort:skip
from shared.shared_types import A11yElement  # isort:skip
import shared.config as config  # isort:skip
import gi
from lib import Singleton, InterruptableThread, AtspiEvent, get_states
import time


class Desktop(Singleton):
    @staticmethod
    def getRoot(specific_app: Optional[str] = None):
        desktop = pyatspi.Registry.getDesktop(0)
        for app in desktop:
            for window in app:
                states = get_states(window)
                ACTIVE = window.getState().contains(pyatspi.STATE_ACTIVE)
                # Active should not be used for objects which have State::Focusable or State::Selectable:
                # Those objects should use State::Focused and State::Selected respectively.

                FOCUSABLE = window.getState().contains(pyatspi.STATE_FOCUSED)
                SELECTABLE = window.getState().contains(pyatspi.STATE_SELECTED)

                if ACTIVE:
                    # logging.debug(f"{app.get_name()} {states}")
                    return app, window

                if specific_app and specific_app == app.get_name():
                    return app, window

        else:
            logging.debug(
                f"No root window found among {[app.get_name() for app in desktop]}"
            )

        return (None, None)


class A11yTree(Singleton):
    constructor_handle: Optional[InterruptableThread] = None

    element_mapper: Optional[dict[A11yElement, pyatspi.Accessible]] = None

    @classmethod
    def get_elements(
        cls, parent_app: str, root, accumulator: dict[A11yElement : pyatspi.Accessible]
    ) -> list[A11yElement]:
        """
        Recursive method for creating the a11y tree within the separate creator thread.
        In a thread so it doesn't block when the user switches the focused app
        """
        if not root or cls.constructor_handle.interrupted():
            return accumulator

        try:
            for accessible in root:
                accessible: pyatspi.Accessible
                if not accessible:
                    continue

                point = accessible.get_position(pyatspi.XY_SCREEN)
                states = accessible.get_state_set()
                # https://docs.gtk.org/atspi2/enum.StateType.html
                visible = states.contains(pyatspi.STATE_VISIBLE)
                sensitive = states.contains(pyatspi.STATE_SENSITIVE)
                focusable = states.contains(pyatspi.STATE_FOCUSABLE)
                showing = states.contains(pyatspi.STATE_SHOWING)

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
                f"Error while creating a11y tree for {parent_app} with root {root}: {ge}"
            )

        return accumulator

    @classmethod
    def reset(cls):
        # if cls.constructor_handle:
        #     cls.constructor_handle.interrupt()
        #     logging.debug("Construct handle removed")
        #     cls.constructor_handle = None
        pass

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
        old_app = "NULL" if old_app is None else old_app.get_name()

        # tree_action = "interrupting" if cls.constructor_handle else "starting"
        logging.debug(
            f"Tree dump {'starting'} with {(event.type)} from {event.source} inside {old_app} with root: {old_root}"
        )

        new_app_name = event.source.get_application().get_name()

        _, new_app_root = Desktop.getRoot(new_app_name)

        A11yTree.reset()

        A11yTree.constructor_handle = InterruptableThread(
            target=A11yTree.get_elements, args=(new_app_name, new_app_root, {})
        )

        """
        We need to start then join the thread to have an interruptable blocking operation.
        If the user focused another window, we want to stop the construction and the block on
        the creation of the new tree for the new window
        """
        A11yTree.constructor_handle.start()

        elements: dict[A11yElement, pyatspi.Accessible] = (
            A11yTree.constructor_handle.join()
        )

        assert elements is not None

        if A11yTree.constructor_handle.interrupted():
            logging.debug(f"Tree dump interrupted for {new_app_name}")
            return
        elif event.source.getRole() == pyatspi.ROLE_FRAME and len(elements) == 0:
            logging.debug(
                f"Skipped tree dump for internal frame inside {new_app_name} with {len(elements)} elements"
            )
            return
        elif len(elements) == 0 and event.type == pyatspi.EventType("focus"):
            logging.debug(f"Skipped tree dump for pseudo update inside {new_app_name}.")
            return

        # Once the thread is done, get rid of the handle
        A11yTree.constructor_handle = None

        A11yTree.element_mapper = elements

        if os.path.exists(config.TREE_OUTPUT_PATH):
            os.remove(config.TREE_OUTPUT_PATH)

        with open(config.TREE_OUTPUT_PATH, "w") as outfile:
            entire_tree_serialized = [element.to_dict() for element in elements.keys()]
            json.dump(entire_tree_serialized, outfile)

        delta = round(time.time() - start, 2)

        logging.debug(f"Dumped tree with {len(elements)} elements in {delta} seconds")
