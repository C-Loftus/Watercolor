# from talon.canvas import Canvas
# from talon.types import Rect
# from talon import ui
# from talon.skia.canvas import Canvas as SkiaCanvas

# def on_draw(c: SkiaCanvas):
#     c.paint.color = "FF0000"
#     c.paint.style = c.paint.Style.FILL
#     c.draw_rect(Rect(100,100,100,100))
#     c.draw_text("Hello, World!", 100, 100)

# screen: ui.Screen = ui.main_screen()

# # Create a canvas object that you can draw or add text to
# canvas = Canvas.from_screen(screen)
# canvas.blocks_mouse = False

# # Add a callback to specify how the canvas should be drawn
# canvas.register("draw", on_draw)

# # Freeze the canvas so it doesn't repeatedly refresh
# canvas.freeze()