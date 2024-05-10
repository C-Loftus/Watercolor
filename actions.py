from talon import Module, Context

from .renderer import WatercolorState, ScreenLabels, paintTree

mod = Module()
ctx = Context()
ctx.matches = r"""
os: linux
"""


mod.list("watercolor_hats", desc="The active hats over every a11y element")


def _construct_hat_list():
    ctx.lists["user.watercolor_hats"] = {
        ScreenLabels.points[1]
    }



@mod.action_class
class Actions:
    def watercolor_toggle_hats():
        """Toggle showing hats over every a11y element each time the screen state changes"""

        if WatercolorState.enabled:
            ScreenLabels.clear()
            WatercolorState.enabled = False
        else:
            paintTree(None)
            WatercolorState.enabled = True
            
    def watercolor_toggle_debug():
        """Toggle showing the debug hats over every a11y element each time the screen state changes"""

        WatercolorState.debug = not WatercolorState.debug
