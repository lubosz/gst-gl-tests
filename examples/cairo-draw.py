#!/usr/bin/env python3

import math
import cairo

WIDTH, HEIGHT = 256, 256

from IPython import embed

#embed()

surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH, HEIGHT)
ctx = cairo.Context(surface)

ctx.scale(WIDTH, HEIGHT)

pat = cairo.LinearGradient(0.0, 0.0, 0.0, 1.0)
# First stop, 50% opacity
pat.add_color_stop_rgba(1, 0.7, 0, 0, 0.5)
# Last stop, 100% opacity
pat.add_color_stop_rgba(0, 0.9, 0.7, 0.2, 1)

# Rectangle(x0, y0, x1, y1)
ctx.rectangle(0, 0, 1, 1)
ctx.set_source(pat)
ctx.fill()

# Changing the current transformation matrix
ctx.translate(0.1, 0.1)

ctx.move_to (0, 0)
ctx.arc (0.2, 0.1, 0.1, -math.pi/2, 0) # Arc(cx, cy, radius, start_angle, stop_angle)
ctx.line_to (0.5, 0.1) # Line to (x,y)
ctx.curve_to (0.5, 0.2, 0.5, 0.4, 0.2, 0.8) # Curve(x1, y1, x2, y2, x3, y3)
ctx.close_path ()

ctx.set_source_rgb (0.3, 0.2, 0.5) # Solid color
ctx.set_line_width (0.02)
ctx.stroke ()

surface.write_to_png ("example.png") # Output to PNG

#embed()
