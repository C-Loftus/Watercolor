
import gi.repository
import pyatspi
import json
import os
import logging
import dataclasses
from typing import ClassVar, Optional
import sys
sys.path.append(".") # Adds higher directory to python modules path.
from shared.shared_types import A11yElement
import shared.config as config
import gi

import threading

class StoppableThread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self,  *args, **kwargs):
        super(StoppableThread, self).__init__(*args, **kwargs)
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()



class Desktop():
   
    @staticmethod
    def getRoot():
        desktop = pyatspi.Registry.getDesktop(0)
        for app in desktop:
            for window in app:
                logging.debug(f"States for {window}: {list(window.get_state_set().get_states())}")
                if window.getState().contains(pyatspi.STATE_ACTIVE):
                    return window
                
        else:
            logging.warning(f"No active window found among {[app.get_name() for app in desktop]}")

    
    # libatspi does not export a way to get a public unique id
    # so we need to serialize the above attributes as a psuedo id
    # id: str

class A11yTree():

    constructor_handle: Optional[StoppableThread] = None
    
    _elements: ClassVar[list[A11yElement]] = []

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

            # if not EXISTS_ALREADY and not OFF_SCREEN and INTERACTABLE:
            
            A11yTree._create(accessible)
            
        
    @classmethod
    def reset(cls):
        if cls.constructor_handle:
            print("Stopping")
            cls.constructor_handle.stop()
            cls.constructor_handle = None
            

        cls._elements = []
      
    @staticmethod
    def dump(event):

        '''
        Event fields:

        'any_data', 'copy', 'detail1', 'detail2', 'host_application', 'main', 'quit', 'rawType', 'sender', 'source', 'source_name', 'source_role', 'type']
        '''
        print(event)
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

        print(f"Dumped tree for {root} with {len(A11yTree._elements)} elements")



