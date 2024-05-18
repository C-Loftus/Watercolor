# from talon.canvas import Canvas
# from talon.types import Rect
# from talon import ui
# from talon.skia.canvas import Canvas as SkiaCanvas

# def on_draw(c: SkiaCanvas):
#     c.paint.color = "FF0000"
#     c.paint.style = c.paint.Style.FILL
#     print(dir(c.paint.typeface.fontstyle.weight))
#     print((c.paint.typeface.font_width.to_bytes()))
#     c.draw_rect(Rect(100,100,100,100))
#     # c.paint.typeface.font_width = 100
#     # c.paint.typeface.fontstyle.weight = 100
#     c.draw_text("Hello, World!", 100, 100)

# screen: ui.Screen = ui.main_screen()

# # Create a canvas object that you can draw or add text to
# canvas = Canvas.from_screen(screen)
# canvas.draggable = False
# canvas.blocks_mouse = False
# canvas.focused = False
# canvas.cursor_visible = True

# # Add a callback to specify how the canvas should be drawn
# canvas.register("draw", on_draw)

# # Freeze the canvas so it doesn't repeatedly refresh
# canvas.freeze()