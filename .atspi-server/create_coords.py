
import pyatspi
import json
import os
import logging
import dataclasses
from typing import ClassVar
import base64
from ..shared import config

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


@dataclasses.dataclass
class A11yElement():
    name: str
    x: int
    y: int
    role: str
    pid: int
    
    # libatspi does not export a way to get a public unique id
    # so we need to serialize the above attributes as a psuedo id
    # id: str

class A11yTree():
    
    _elements: ClassVar[list[A11yElement]] = []

    @staticmethod
    def _append_element(element: A11yElement): 
        A11yTree._elements.append(element)
    
    @staticmethod
    def element_exists(element: A11yElement):
        return element in A11yTree._elements
      
    @staticmethod
    def _create(root):
        if not root: return


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

            A11yTree._create(accessible)
            

 
        
    @classmethod
    def reset(cls):
        cls._elements = []
      
    @staticmethod
    def dump(event):

        '''
        Event fields:

        'any_data', 'copy', 'detail1', 'detail2', 'host_application', 'main', 'quit', 'rawType', 'sender', 'source', 'source_name', 'source_role', 'type']
        '''
        
        root = Desktop.getRoot()
   
        A11yTree.reset()
        A11yTree._create(root)

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



