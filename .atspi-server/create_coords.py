
import pyatspi
import json
import os
import logging
 
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
                logging.info(f"States for {window}: {list(window.get_state_set().get_states())}")
                if window.getState().contains(pyatspi.STATE_ACTIVE):
                    return window
                
        else:
            print("No active window found")

class A11yTree():
    
    elements = []
    _point_lookup = {}
    _id_lookup = {}
    

    @staticmethod
    def _add_element(name, id, x, y): 
        A11yTree.elements.append({"name": name, "x": x, "y": y})
        A11yTree._point_lookup[(x, y)] = True
        A11yTree._id_lookup[id] = True

    def point_exists(x, y):
        return A11yTree._point_lookup.get((x, y), False)
    
    def id_exists(id):
        return A11yTree._id_lookup.get(id, False)
      
    @staticmethod
    def _create(root):
        if not root: return

        try:
            
            for accessible in root: 
                accessible: pyatspi.Accessible
                if not accessible: continue

                point = accessible.get_position(pyatspi.XY_SCREEN)
                states = accessible.get_state_set() 
                logging.info(f"States for {accessible}: {list(states.get_states())}")
                # https://docs.gtk.org/atspi2/enum.StateType.html
                 
                visible = states.contains(pyatspi.STATE_VISIBLE)
                sensitive = states.contains(pyatspi.STATE_SENSITIVE)
                focusable = states.contains(pyatspi.STATE_FOCUSABLE)
                showing = states.contains(pyatspi.STATE_SHOWING)

                if visible and showing and (sensitive or focusable):
                    name = accessible.get_name() 
                    id = accessible.get_accessible_id()
                    x = point.x
                    y = point.y

                    if  (x > -2000 and y > -2000) and not A11yTree.point_exists(x, y) and  name != None:
                        if name != "":
                            A11yTree._add_element(name,id, x, y)
                            
                A11yTree._create(accessible)
               

        except Exception as e:
            logging.error("Error skipping tree creation due to: " + str(e))
            return
        
    @classmethod
    def reset(cls):
        cls.elements = []
        cls._point_lookup = {}
        cls._id_lookup = {}
      
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
        if len(A11yTree.elements) == 0 and event.type == pyatspi.EventType('focus'):
            return

        print(f"Dumped tree with {len(A11yTree.elements)} elements")
        
        try:
            os.remove('/tmp/a11y_tree.json')
        except:
            logging.debug("Trying to remove /tmp/a11y_tree.json but it was already removed")

        with open('/tmp/a11y_tree.json', 'w') as outfile:
            json.dump(A11yTree.elements, outfile)



