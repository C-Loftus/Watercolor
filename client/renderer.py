from .client_types import WatercolorState
from talon import resource, Context
import pathlib, os, json
from talon.canvas import Canvas
from talon.types import Rect
from talon import ui
from talon.skia.canvas import Canvas as SkiaCanvas
from talon import skia
from talon.skia.imagefilter import ImageFilter
import itertools
from typing import ClassVar
from ..shared.shared_types import A11yElement
from ..shared import config
import time

import itertools


def generate_combinations(l):
    return ["".join(i) for i in list(itertools.product(*([l] * 2)))]


alphabet = generate_combinations(list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))

FOREGROUND_TEXT_COLOR = "1f2335"
BACKGROUND_COLOR = "7aa2f7"
HAT_RADIUS = 14
PERCENT_TRANSPARENCY = 0.5

ctx = Context()


def get_color() -> str:
    color_alpha = f"{(int((1- PERCENT_TRANSPARENCY) * 255)):02x}"
    return f"{BACKGROUND_COLOR}{color_alpha}"


def _on_draw(c: SkiaCanvas):
    # c.paint.imagefilter = ImageFilter.drop_shadow(1, 1, 1, 1, color_gradient)

    for label, element in ScreenLabels.element_mapping.items():
        # c.paint.shader = skia.Shader.radial_gradient(
        #      (x, y), HAT_RADIUS, [get_color(), 255]
        #      )
        c.paint.color = get_color()
        c.paint.style = c.paint.Style.FILL
        c.draw_rect(
            Rect(
                element.x - HAT_RADIUS,
                element.y - HAT_RADIUS,
                HAT_RADIUS * 2,
                HAT_RADIUS * 1.5,
            )
        )
        c.paint.color = FOREGROUND_TEXT_COLOR
        c.paint.style = c.paint.Style.FILL
        c.paint.stroke_width = 3
        c.draw_text(label, element.x - (0.5 * HAT_RADIUS), element.y)


class ScreenLabels:
    element_mapping: ClassVar[dict[A11yElement, str]] = {}
    canvas: ClassVar[Canvas] = None

    @classmethod
    def clear(cls):
        if cls.canvas:
            cls.canvas.close()
            cls.canvas.unregister("draw", _on_draw)
            cls.canvas = None

        cls.element_mapping = {}

    @classmethod
    def add(cls, element: A11yElement, text: str = None):
        text = alphabet[len(cls.element_mapping)] if not text else text
        cls.element_mapping[text] = element

    @classmethod
    def render(cls):
        screen: ui.Screen = ui.main_screen()

        cls.canvas = Canvas.from_screen(screen)
        cls.canvas.draggable = False
        cls.canvas.blocks_mouse = False
        cls.canvas.focused = False
        cls.canvas.cursor_visible = True

        cls.canvas.register("draw", _on_draw)
        cls.canvas.freeze()

    @classmethod
    def get_element_from_label(cls, label: str) -> A11yElement:
        return cls.element_mapping[label]


class A11yTree:
    # get the absolute path of the current file
    ipc_path: ClassVar[pathlib.Path] = pathlib.Path(
        os.path.abspath(config.TREE_OUTPUT_PATH)
    )

    @classmethod
    def getElements(cls) -> list[A11yElement]:
        with open(cls.ipc_path) as f:
            raw = json.load(f)

            return [
                A11yElement(
                    element["name"],
                    element["x"],
                    element["y"],
                    element["role"],
                    element["pid"],
                )
                for element in raw
            ]


@resource.watch(A11yTree.ipc_path)
def renderElementStyling(_):
    # if not os.path.exists(A11yTree.ipc_path):
    # raise Exception(f"File {A11yTree.ipc_path=} was updated but now does not exist")
    # start the timer

    start = time.time()

    elements: list[A11yElement] = A11yTree.getElements()
    ScreenLabels.clear()

    for element in elements:
        ScreenLabels.add(element)

    if not WatercolorState.enabled:
        return

    ScreenLabels.render()

    print(f"Rendered in {round(time.time() - start, 3)} seconds")
