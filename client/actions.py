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

    def watercolor_action(action_name: str, target_label: str):
        """Apply the specified element to the specified target"""
        try:
            payload = {
                "command": "",
                "target": ScreenLabels.get_element_from_label(target_label).to_dict()
            }
        except KeyError:
            print(f"Error: {target_label} not found in", ScreenLabels.element_mapping)
            return


        if action_name == "click":
            payload["command"] = "click"
        elif action_name == "inspect":
            payload["command"] = "inspect"
        else:
            raise Exception(f"Invalid action: {action_name}")

        actions.user.send_watercolor_command(payload)

    