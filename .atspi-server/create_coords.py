
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
from lib import Singleton, StoppableThread, AtspiEvent
import time

class Desktop(Singleton):
   
    @staticmethod
    def getRoot():
        desktop = pyatspi.Registry.getDesktop(0)

        for app in desktop:
            for window in app:
                logging.debug(f"States for {window}: {list(window.get_state_set().get_states())}")
                # print(f"\n\nStates for {window}: {[str(state) for state in list(window.get_state_set().get_states())]}")
                if window.getState().contains(pyatspi.STATE_ACTIVE):
                    return window
                
        else:
            print(f"No active window found among {[app.get_name() for app in desktop]}")

class A11yTree(Singleton):

    constructor_handle: Optional[StoppableThread] = None
    
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
        if not root or cls.constructor_handle.stopped(): 
            return

        for accessible in root: 
            accessible: pyatspi.Accessible
            if not accessible: continue

            point = accessible.get_position(pyatspi.XY_SCREEN)
            states = accessible.get_state_set() 
            logging.debug(f"States for {accessible}: {list(states.get_states())}")
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
            cls.constructor_handle.stop()
            cls.constructor_handle = None
            
        cls._serialized_mapper = {}
        cls._elements = []
      
    @staticmethod
    def dump(event: AtspiEvent):

        root = Desktop.getRoot()

        A11yTree.reset()

        A11yTree.constructor_handle = StoppableThread(target=A11yTree._create, args=(root, ))
    
        """
        We need to start then join the thread to have an interruptable blocking operation.
        If the user focused another window, we want to stop the construction and the block on
        the creation of the new tree for the new window
        """
        A11yTree.constructor_handle.start()
        A11yTree.constructor_handle.join()

        # don't regenerate the hats if Firefox performed a psuedo focus where nothing actually changed on the screen
        if len(A11yTree._elements) == 0 and event.type == pyatspi.EventType('focus'):
            return
        
        try:
            os.remove(config.TREE_OUTPUT_PATH)
        except:
            logging.debug(f"Trying to remove {config.TREE_OUTPUT_PATH} but it was already removed")

        with open(config.TREE_OUTPUT_PATH, 'w') as outfile:

            entire_tree_serialized = [
                dataclasses.asdict(element) for element in A11yTree._elements]
            
            # b64_tree = base64.b64encode(json.dumps(entire_tree_serialized).encode('utf-8'))


            # outfile.write(str(b64_tree))

            json.dump(entire_tree_serialized, outfile)

        print(f"Dumped tree for {(event.type)} from {event.source} inside {root} with {len(A11yTree._elements)} elements")



