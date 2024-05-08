from talon import resource
import pathlib, os, json
from typing import TypedDict
from talon.canvas import Canvas
from talon.types import Rect
from talon import ui
from talon.skia.canvas import Canvas as SkiaCanvas 
from talon import skia
from talon.skia.imagefilter import ImageFilter
import itertools

alphabet = [''.join(comb) for comb in itertools.combinations('ABCDEFGHIJKLMNOPQRSTUVWXYZ123456789', 4)]

FOREGROUND_TEXT_COLOR = "1f2335"
BACKGROUND_COLOR = "7aa2f7" 
HAT_RADIUS = 14
PERCENT_TRANSPARENCY = 0.5

def get_alpha_color() -> str:
    return f"{(int((1- PERCENT_TRANSPARENCY) * 255)):02x}"
    
def get_color():
    color_alpha = get_alpha_color()
    return f"{BACKGROUND_COLOR}{color_alpha}"


class A11yElement(TypedDict):
    name: str
    x: int
    y: int

def on_draw(c: SkiaCanvas):



    # c.paint.imagefilter = ImageFilter.drop_shadow(1, 1, 1, 1, color_gradient)

    for (x, y, text) in ScreenLabels.points:
            # c.paint.shader = skia.Shader.radial_gradient(
            #      (x, y), HAT_RADIUS, [get_color(), 255]
            #      )
            c.paint.color = get_color()
            c.paint.style = c.paint.Style.FILL
            c.draw_rect(
                Rect(
                        x - HAT_RADIUS,
                        y - HAT_RADIUS,
                        HAT_RADIUS * 2,
                        HAT_RADIUS * 2,
                )
            )
            c.paint.color = FOREGROUND_TEXT_COLOR
            c.paint.style = c.paint.Style.FILL
            c.paint.stroke_width = 3
            c.draw_text(text, x - HAT_RADIUS, y)

class ScreenLabels():
    
    points: list[tuple[int, int]] = []
    canvas: Canvas = None

    @classmethod
    def clear(cls):
        if not cls.canvas:
            return

        cls.canvas.close()
        cls.canvas.unregister("draw", on_draw)
        cls.canvas = None
        cls.points = []
        
    
    @classmethod
    def add(cls, x, y):
        cls.points.append((x, y, alphabet[len(cls.points)]))

    @classmethod
    def render(cls):
        cls.clear()

        screen: ui.Screen = ui.main_screen()

        cls.canvas = Canvas.from_screen(screen)
        cls.canvas.draggable = False
        cls.canvas.blocks_mouse = False
        cls.canvas.focused = False
        cls.canvas.cursor_visible = True

        cls.canvas.register("draw", on_draw)
        cls.canvas.freeze()




class A11yTree():
    # get the absolute path of the current file
    ipc_path = pathlib.Path(os.path.abspath("/tmp/a11y_tree.json"))
    
    @classmethod
    def getElements(cls) -> list[A11yElement]:
        with open(cls.ipc_path) as f:
            return json.load(f)


@resource.watch(A11yTree.ipc_path)
def paintTree(_):
    elements: list[A11yElement] = A11yTree.getElements()
    ScreenLabels.clear()

    for element in elements:
        ScreenLabels.add(element["x"], element["y"])

    ScreenLabels.render()