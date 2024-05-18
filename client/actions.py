from talon import Module, Context, actions
import dataclasses, json
from .renderer import WatercolorState, ScreenLabels, renderElementStyling, A11yTree

mod = Module()
ctx = Context()
ctx.matches = r"""
os: linux
"""


@mod.capture(
    rule="<user.letter> <user.letter>"
)
def watercolor_hint(m) -> str:
    print(m)
    # remove all spaces inside the hint
    return "".join(m).replace(" ", "").upper()


@mod.action_class
class Actions:
    def watercolor_toggle_hats():
        """Toggle showing hats over every a11y element each time the screen state changes"""

        if WatercolorState.enabled:
            ScreenLabels.clear()
            WatercolorState.enabled = False
            print("Watercolor disabled")
        else:
            renderElementStyling(None)
            WatercolorState.enabled = True
            print("Watercolor enabled")
            
    def watercolor_toggle_debug():
        """Toggle showing the debug hats over every a11y element each time the screen state changes"""

        WatercolorState.debug = not WatercolorState.debug

    def watercolor_click(label: str):
        """Apply the specified element to the specified target"""
        res = (ScreenLabels.get_element_from_label(label).to_dict())
        payload = {
            "command": "click",
            "target": res
        }
        actions.user.send_watercolor_command(payload)