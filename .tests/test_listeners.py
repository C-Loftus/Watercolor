#!/usr/bin/python3

# TODO: figure out a way to test this in headless CI environment.
# For time being mainly used to determine what events are being
# output by each window

import gi

gi.require_version("Atspi", "2.0")
from gi.repository import Atspi

try:
    for event in [
        "window:activate",
        "window:create",
        "window:destroy",
        "window:maximize",
        "window:minimize",
        "window:move",
        # Can't use the object changed events since the tree sometimes does child changes
        # that don't actually affect the user interaction. Sometimes it outputs many changes and
        # triggers and infinite loop
        # "object:children-changed:add",
        # "object:children-changed:remove",
        "object:visible-data-changed",
        "object:row-reordered",
        "object:column-reordered",
        "object:state-changed:expanded",
        "object:state-changed:focused",  # Used for firefox tab switching
        "document:page-changed",
        "document:load-complete",
        "document:page-changed",
        "document:attributes-changed",
        "document:reload",
    ]:
        listener: Atspi.EventListener = Atspi.EventListener.new(lambda x: print(x))
        Atspi.EventListener.register(listener, event)

    Atspi.Event.main()
except:
    Atspi.Event.quit()
