from typing import Literal
from talon import Module, Context, actions, app
import dataclasses, json
from .renderer import WatercolorState, ScreenLabels, renderElementStyling, A11yTree
from ..shared.shared_types import WatercolorCommand

mod = Module()
ctx = Context()
ctx.matches = r"""
os: linux
"""

mod.setting("watercolor_foreground_color", type=str, default="F6DCAC")
mod.setting("watercolor_background_color", type=str, default="01204E")
mod.setting("watercolor_hat_radius", type=int, default=14)
mod.setting("watercolor_percent_transparency", type=float, default=0.1)


@mod.capture(rule="<user.letter> <user.letter>")
def watercolor_hint(m) -> str:
    # remove all spaces inside the hint
    return "".join(m).replace(" ", "").upper()


@mod.action_class
class Actions:
    def watercolor_refresh():
        """Refresh the screen state"""
        WatercolorState.enabled = True
        ScreenLabels.refresh()

    def watercolor_toggle_hats():
        """Toggle showing hats over every a11y element each time the screen state changes"""

        if WatercolorState.enabled:
            ScreenLabels.clear()
            WatercolorState.enabled = False
            print("Watercolor disabled")
            app.notify("Watercolor disabled")
        else:
            renderElementStyling(_ := None)
            WatercolorState.enabled = True
            print("Watercolor enabled")
            app.notify("Watercolor enabled")
            ScreenLabels.render()

    def watercolor_toggle_debug():
        """Toggle showing the debug hats over every a11y element each time the screen state changes"""

        WatercolorState.debug = not WatercolorState.debug

    def watercolor_action(action_name: str, target_label: str):
        """Apply the specified element to the specified target"""
        try:
            payload = {
                "command": "",
                "target": ScreenLabels.get_element_from_label(target_label).to_dict(),
            }
        except KeyError:
            raise KeyError(
                f"Error: {target_label} not found in", ScreenLabels.element_mapping
            )

        match action_name:
            case "click" | "inspect" as valid_action:
                payload["command"] = valid_action
            case _:
                raise Exception(f"Invalid action: {action_name}")
        print(payload)
        actions.user.send_watercolor_command(payload)
