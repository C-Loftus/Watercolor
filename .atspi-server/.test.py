from talon.canvas import Canvas
from talon.types import Rect
from talon import ui
from talon.skia.canvas import Canvas as SkiaCanvas 

def on_draw(c: SkiaCanvas):
    c.paint.color = "FF0000"
    c.paint.style = c.paint.Style.FILL
    c.draw_rect(Rect(100,100,100,100))

screen: ui.Screen = ui.main_screen()

canvas = Canvas.from_screen(screen)
canvas.draggable = False
canvas.blocks_mouse = False
canvas.focused = False
canvas.cursor_visible = True

canvas.register("draw", on_draw)
canvas.freeze()



