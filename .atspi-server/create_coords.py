
import gi.repository
from gi.repository import Atspi
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
from lib import Singleton, InterruptableThread, AtspiEvent
import time

class Desktop(Singleton):
   
    @staticmethod
    def getRoot():
        desktop = pyatspi.Registry.getDesktop(0)
        
        for app in desktop:
            for window in app:
                # print(f"\n\nStates for {window}: {[str(state) for state in list(window.get_state_set().get_states())]}")
                if window.getState().contains(pyatspi.STATE_ACTIVE):
                    return app, window
                
        else:
            logging.debug(f"No active window found among {[app.get_name() for app in desktop]}")

        return (None, None)

class A11yTree(Singleton):

    constructor_handle: Optional[InterruptableThread] = None
    
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
    def _create(cls, root):
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


            INTERACTABLE = visible and showing and (sensitive or focusable)

            x = point.x
            y = point.y
            # parent_application = accessible.get_application().get_name()
            pid = accessible.get_process_id()
            role = accessible.get_role_name()
            name = accessible.get_name() 
            element = A11yElement(name, x, y, role, pid)

            OFF_SCREEN = x < -2000 or y < -2000

            UNLABELED = name == ""

            EXISTS_ALREADY = A11yTree.element_exists(element)

            if INTERACTABLE and not EXISTS_ALREADY and not OFF_SCREEN and not UNLABELED:
                A11yTree._append_element(element)  
                A11yTree._stash_accessible(element, accessible) 

            # if not EXISTS_ALREADY and not OFF_SCREEN and INTERACTABLE:
            A11yTree._create(accessible)
            
        
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

        app, root = Desktop.getRoot()
        app = "NULL" if app is None else app.get_name()



        tree_action = "interrupting" if cls.constructor_handle else "starting"
        logging.debug(f"Tree dump {tree_action} with {(event.type)} from {event.source} inside {root}")

        A11yTree.reset()

        assert cls.constructor_handle is None

        A11yTree.constructor_handle = InterruptableThread(target=A11yTree._create, args=(root, ))

    
        """
        We need to start then join the thread to have an interruptable blocking operation.
        If the user focused another window, we want to stop the construction and the block on
        the creation of the new tree for the new window
        """
        A11yTree.constructor_handle.start()
        A11yTree.constructor_handle.join()
        if A11yTree.constructor_handle.interrupted():
            logging.debug(f"Tree dump interrupted for {app}")
            return
        
        # Once the thread is done, get rid of the handle
        A11yTree.constructor_handle = None

        # don't regenerate the hats if Firefox performed a psuedo focus where nothing actually changed on the screen
        FROM_INTERNAL_FRAME = event.source.getRole() == pyatspi.ROLE_FRAME
        PSEUDO_UPDATE = len(A11yTree._elements) == 0 and event.type == pyatspi.EventType('focus')
        if FROM_INTERNAL_FRAME:
            logging.debug(f"Skipped tree dump for internal frame inside {app} with {len(A11yTree._elements)} elements")
            return

        if PSEUDO_UPDATE:
            logging.debug(f"Skipped tree dump for pseudo update inside {app}.")
            return
        
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



