#!/usr/bin/python
import pyatspi
import itertools
import json
 

alphabet = [''.join(comb) for comb in itertools.combinations('ABCDEFGHIJKLMNOPQRSTUVWXYZ', 2)]

class FocusedWindow():
   
    @staticmethod
    def getRoot():
        desktop = pyatspi.Registry.getDesktop(0)
        for app in desktop:
            for window in app:
                if window.getState().contains(pyatspi.STATE_ACTIVE):
                    return window

class A11yTree():
    
    elements = []

    @staticmethod
    def _add_element(name, x, y): 
        A11yTree.elements.append({"name": name, "x": x, "y": y})
      
    @staticmethod
    def _create(root):
        if not root: return

        try: 
            iter(root)
        except:
            return

        for tree in root: 
                if not tree: continue

                point = tree.get_position(pyatspi.XY_SCREEN)
                states = tree.get_state_set()
                if (states.contains(pyatspi.STATE_FOCUSABLE)) and (states.contains(pyatspi.STATE_VISIBLE)):
                    name = tree.get_name() 
                    x = point.x
                    y = point.y
                    if x < -2000 or y < -2000:
                        continue

                    A11yTree._add_element(name, x, y)

                if (tree.get_state_set().contains(pyatspi.STATE_VISIBLE)):
                    A11yTree._create(tree)
      
    @staticmethod
    def dump(_):
        A11yTree._create(FocusedWindow.getRoot())

        with open('/tmp/a11y_tree.json', 'w') as outfile:
            json.dump(A11yTree.elements, outfile)



for event in ["window:activate", "window:create", "window:deactivate", "window:destroy", "window:maximize", "window:minimize", "window:move", "focus", "object:visible-data-changed"]:
  pyatspi.Registry.registerEventListener(A11yTree.dump, event)

pyatspi.Registry.start()