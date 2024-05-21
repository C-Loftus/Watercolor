
import gi.repository
import pyatspi
import json
import os
import logging
import dataclasses
from typing import ClassVar, Optional
import sys # isort:skip
sys.path.append(".") # isort:skip
from shared.shared_types import A11yElement # isort:skip
import shared.config as config # isort:skip
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
            logging.debug(f"No root window found among {[app.get_name() for app in desktop]}")

        return (None, None)


class A11yTree(Singleton):

    constructor_handle: Optional[InterruptableThread] = None

    cached_a11y_dump = None
    
    _elements: ClassVar[list[A11yElement]] = []

    # Map our serializiable representation of an element to the actual Atspi element
    # upon which actions can be invoked
    _serialized_mapper: ClassVar[dict[A11yElement, pyatspi.Accessible]] = {}


    @classmethod
    def get_accessible_from_element(cls, element: A11yElement):
        return cls._serialized_mapper.get(element)

    @classmethod
    def _stash_accessible(cls, element: A11yElement, accessible: pyatspi.Accessible):
        cls._serialized_mapper[element] = accessible

    @staticmethod
    def _append_element(element: A11yElement): 
        A11yTree._elements.append(element)
        
    
    @staticmethod
    def element_exists(element: A11yElement):
        return element in A11yTree._elements
      
    @classmethod
    def _create(cls, root_application, root):
        """
        Recursive method for creating the a11y tree within the separate creator thread.
        In a thread so it doesn't block when the user switches the focused app
        """
        if not root or cls.constructor_handle.interrupted(): 
            return

        for accessible in root: 
            accessible: pyatspi.Accessible
            if not accessible: continue

            point = accessible.get_position(pyatspi.XY_SCREEN)
            states = accessible.get_state_set() 
            # https://docs.gtk.org/atspi2/enum.StateType.html
                
            visible = states.contains(pyatspi.STATE_VISIBLE)
            sensitive = states.contains(pyatspi.STATE_SENSITIVE)
            focusable = states.contains(pyatspi.STATE_FOCUSABLE)
            showing = states.contains(pyatspi.STATE_SHOWING)

            # In an ideal world, we should only need to use focusable here. 
            # However, many applications don't apply focusable on elements that 
            # should be focusable, so it is better to check both and have too much
            # instead of too little
            INTERACTABLE: bool 
            # these apps actually implements atspi properly, while most other apps do not
            match root_application:
                case "code":
                    INTERACTABLE = visible and showing and (focusable)
                # Firefox doesn't add focusable to certain dom elements that should be focusable.
                case "firefox" | _ :
                    INTERACTABLE= visible and showing and (focusable or sensitive)

            x = point.x
            y = point.y
            # parent_application = accessible.get_application().get_name()
            pid = accessible.get_process_id()
            role = accessible.get_role_name()
            name = accessible.get_name() 
            element = A11yElement(name, x, y, role, pid)

            # OFF_SCREEN = x < -2000 or y < -2000

            UNLABELED = name == ""

            EXISTS_ALREADY = A11yTree.element_exists(element)

            if INTERACTABLE and not EXISTS_ALREADY and not UNLABELED: #and not OFF_SCREEN
                A11yTree._append_element(element)  
                A11yTree._stash_accessible(element, accessible) 

            # if not EXISTS_ALREADY and not OFF_SCREEN and INTERACTABLE:
            A11yTree._create(root_application, accessible)
            
        
    @classmethod
    def reset(cls):
        if cls.constructor_handle:
            cls.constructor_handle.interrupt()
            logging.debug("Construct handle removed")
            cls.constructor_handle = None
            
        cls._serialized_mapper = {}
        cls._elements = []
      
    @classmethod
    def dump(cls, event: AtspiEvent):

        start = time.time()

        """
        At the time window:activate is output, the old_app is currently still focused. 
        So we need to look for the source of the window:activate event to find the new
        focused app
        """
        old_app, old_root = Desktop.getRoot()
        old_app = "NULL" if old_app is None else old_app.get_name()

        tree_action = "interrupting" if cls.constructor_handle else "starting"
        logging.debug(f"Tree dump {tree_action} with {(event.type)} from {event.source} inside {old_app} with root: {old_root}")

        new_app_name = event.source.get_application().get_name()

        _, new_app_root = Desktop.getRoot(new_app_name)

        A11yTree.reset()

        assert cls.constructor_handle is None


        # TODO: make this recusively return the elements instead of updating them in place. SInce 
        # you want to start the dump inside the app where the window:activate is coming from i.e. the event.source, not the actual root at the time of the event
        A11yTree.constructor_handle = InterruptableThread(target=A11yTree._create, args=(new_app_name, new_app_root, ))

        """
        We need to start then join the thread to have an interruptable blocking operation.
        If the user focused another window, we want to stop the construction and the block on
        the creation of the new tree for the new window
        """
        A11yTree.constructor_handle.start()
        A11yTree.constructor_handle.join()
        if A11yTree.constructor_handle.interrupted():
            logging.debug(f"Tree dump interrupted for {new_app_name}")
            return
        
        # Once the thread is done, get rid of the handle
        A11yTree.constructor_handle = None

        FROM_INTERNAL_FRAME = event.source.getRole() == pyatspi.ROLE_FRAME
        if FROM_INTERNAL_FRAME and len(A11yTree._elements) == 0:
            logging.debug(f"Skipped tree dump for internal frame inside {new_app_name} with no new elements")
            return

        # don't regenerate the hats if Firefox performed a psuedo focus where nothing actually changed on the screen
        PSEUDO_UPDATE = len(A11yTree._elements) == 0 and event.type == pyatspi.EventType('focus')
        if PSEUDO_UPDATE:
            logging.debug(f"Skipped tree dump for pseudo update inside {new_app_name}.")
            return
        
        # if A11yTree.cached_a11y_dump == A11yTree._elements:
        #     logging.debug(f"Skipped tree dump for no change inside {app}.")
        #     return
        # save it in the cache for the next generation
        else:
            A11yTree.cached_a11y_dump = A11yTree._elements

        try:
            os.remove(config.TREE_OUTPUT_PATH)
        except:
            logging.debug(f"Trying to remove {config.TREE_OUTPUT_PATH} but it was already removed")

        with open(config.TREE_OUTPUT_PATH, 'w') as outfile:

            entire_tree_serialized = [
                element.to_dict() for element in A11yTree._elements]


            json.dump(entire_tree_serialized, outfile)

        delta = round(time.time() - start, 2)

        logging.debug(f"Dumped tree with {len(A11yTree._elements)} elements in {delta} seconds")



