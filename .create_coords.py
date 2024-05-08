#!/usr/bin/python
import pyatspi
import json
import os
import logging


try:
    os.remove("atspi_log.txt")
except:
    pass

logging.basicConfig(filename="atspi_log.txt",
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)

logging.info("Running Watercolor")

logger = logging.getLogger('Watercolor')

 
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
            raise RuntimeError("No active window found")

class A11yTree():
    
    elements = []

    @staticmethod
    def _add_element(name, x, y): 
        A11yTree.elements.append({"name": name, "x": x, "y": y})
      
    @staticmethod
    def _create(root):
        if not root: return

        try:
            for tree in root: 
                if not tree: continue

                point = tree.get_position(pyatspi.XY_SCREEN)
                states = tree.get_state_set()
                # https://docs.gtk.org/atspi2/enum.StateType.html
                 
                visible = states.contains(pyatspi.STATE_VISIBLE)
                sensitive = states.contains(pyatspi.STATE_SENSITIVE)
                focusable = states.contains(pyatspi.STATE_FOCUSABLE)

                if visible and (sensitive or focusable):
                    name = tree.get_name() 
                    x = point.x
                    y = point.y

                # if x < -2000 or y < -2000:
                #     continue

                    # print('added')

                A11yTree._add_element(name, x, y)

                A11yTree._create(tree)
               
        except Exception as e:
            logging.error("Error skipping tree creation due to: " + str(e))
            return
      
    @staticmethod
    def dump(event):

        '''
        Event fields:

        'any_data', 'copy', 'detail1', 'detail2', 'host_application', 'main', 'quit', 'rawType', 'sender', 'source', 'source_name', 'source_role', 'type']
        '''
        try:
            root = Desktop.getRoot()
        except RuntimeError:
            return
                    
        A11yTree.elements = []
        A11yTree._create(root)

        # don't regenerate the hats if Firefox performed a psuedo focus where nothing actually changed on the screen
        if len(A11yTree.elements) == 0 and event.type == pyatspi.EventType('focus'):
            return

        print(f"Created a tree with element count = {len(A11yTree.elements)}")
        
        try:
            os.remove('/tmp/a11y_tree.json')
        except:
            logging.debug("Trying to remove /tmp/a11y_tree.json but it was already removed")

        with open('/tmp/a11y_tree.json', 'w') as outfile:
            json.dump(A11yTree.elements, outfile)



for event in ["window:activate", "window:create", "window:deactivate", "window:destroy", "window:maximize", "window:minimize", "window:move", "focus", "object:visible-data-changed"]:
  pyatspi.Registry.registerEventListener(A11yTree.dump, event)

pyatspi.Registry.start()        