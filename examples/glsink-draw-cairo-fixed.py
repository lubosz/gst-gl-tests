#!/usr/bin/env python3

from gi.repository import Gdk
from gi.repository import Gst
from gi.repository import Gtk
from gi.repository import GdkX11    # for window.get_xid()
from gi.repository import GstVideo  # for sink.set_window_handle()

from OpenGL.GL import *

from math import pi

from IPython import embed

import cairo

import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)


class FixedFunctionCairoGL:
    def __init__(self):
        Gdk.init([])
        Gtk.init([])
        Gst.init([])

        self.texture_id = None

        pipeline = Gst.Pipeline()
        src = Gst.ElementFactory.make("videotestsrc", None)
        sink = Gst.ElementFactory.make("glimagesink", None)

        width, height = 1280, 720

        if not sink or not src:
            print("GL elements not available.")
            exit()

        caps = Gst.Caps.from_string("video/x-raw, width=%d, height=%d" % (width, height))
        cf = Gst.ElementFactory.make("capsfilter")
        cf.set_property("caps", caps)

        pipeline.add(src, cf, sink)
        #Gst.Element.link_many(src, cf, sink)
        src.link(cf)
        cf.link(sink)

        window = Gtk.Window()
        window.connect("delete-event", self.window_closed, pipeline)

        window.set_default_size(width, height)
        window.set_title("Hello OpenGL Sink!")

        sink.connect("client-draw", self.draw)
        sink.connect("client-reshape", self.reshape)

        drawing_area = Gtk.DrawingArea()
        window.add(drawing_area)

        window.show_all()
        window.realize()

        xid = drawing_area.get_window().get_xid()
        sink.set_window_handle(xid)

        if pipeline.set_state(Gst.State.PLAYING) == Gst.StateChangeReturn.FAILURE:
            pipeline.set_state(Gst.State.NULL)
        else:
            Gtk.main()

    @staticmethod
    def render_cairo(cr, width, height):
        cr.save()

        # clear background
        cr.set_operator(cairo.OPERATOR_OVER)
        cr.scale(width, height)
        cr.set_source_rgba(0.0, 0.0, 0.25, 1.0)
        cr.paint()

        pat = cairo.LinearGradient(0.0, 0.0, 0.0, 1.0)
        # First stop, 50% opacity
        pat.add_color_stop_rgba(1, 0.7, 0, 0, 0.5)
        # Last stop, 100% opacity
        pat.add_color_stop_rgba(0, 0.9, 0.7, 0.2, 1)

        # Rectangle(x0, y0, x1, y1)
        cr.rectangle(0, 0, 1, 1)
        cr.set_source(pat)
        cr.fill()

        # Changing the current transformation matrix
        cr.translate(0.1, 0.1)

        cr.move_to(0, 0)
        # Arc(cx, cy, radius, start_angle, stop_angle)
        cr.arc(0.2, 0.1, 0.1, -pi/2, 0)
        # Line to (x,y)
        cr.line_to(0.5, 0.1)
        # Curve(x1, y1, x2, y2, x3, y3)
        cr.curve_to(0.5, 0.2, 0.5, 0.4, 0.2, 0.8)
        cr.close_path()

        # Solid color
        cr.set_source_rgb(0.3, 0.2, 0.5)
        cr.set_line_width(0.02)
        cr.stroke()

        cr.restore()

    def reshape(self, sink, context, width, height):
        print("reshape w %d h %d" % (width, height))
        print("OpenGL version:", glGetString(GL_VERSION))
        print("OpenGL vendor:", glGetString(GL_VENDOR))
        print("OpenGL renderer:", glGetString(GL_RENDERER))

        glClearColor(0.0, 0.0, 0.0, 0.0)
        #glDisable(GL_DEPTH_TEST)
        #glEnable(GL_BLEND)
        #glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_TEXTURE_RECTANGLE)

        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        self.cr = cairo.Context(surface)

        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0.0, 1.0, 0.0, 1.0, -1.0, 1.0)

        glClear(GL_COLOR_BUFFER_BIT)

        glActiveTexture(GL_TEXTURE1)

        self.texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_RECTANGLE, self.texture_id)
        self.render_cairo(self.cr, width, height)
        glTexImage2D(GL_TEXTURE_RECTANGLE,
                     0,
                     GL_RGBA,
                     width,
                     height,
                     0,
                     GL_BGRA,
                     GL_UNSIGNED_BYTE,
                     surface.get_data())
        glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_DECAL)

        return True

    def draw(self, sink, context, texture, width, height):

        if not self.texture_id:
                return

        glBindTexture(GL_TEXTURE_2D, texture)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        glBegin(GL_QUADS)
        glTexCoord2f(1.0, 0.0)
        glVertex3f(-1.0, -1.0,  0.0)
        glTexCoord2f(0.0, 0.0)
        glVertex3f(1.0, -1.0,  0.0)
        glTexCoord2f(0.0, 1.0)
        glVertex3f(1.0,  1.0,  0.0)
        glTexCoord2f(1.0, 1.0)
        glVertex3f(-1.0,  1.0,  0.0)
        glEnd()

        #return

        glBindTexture(GL_TEXTURE_RECTANGLE, self.texture_id)

        glBegin(GL_QUADS)

        glTexCoord2f(0.0, 0.0)
        glVertex2f(0.0, 0.0)
        glTexCoord2f(width, 0.0)
        glVertex2f(1.0, 0.0)
        glTexCoord2f(width, height)
        glVertex2f(1.0, 1.0)
        glTexCoord2f(0.0, height)
        glVertex2f(0.0, 1.0)

        glEnd()
        return True

    @staticmethod
    def window_closed(widget, event, pipeline):
        widget.hide()
        pipeline.set_state(Gst.State.NULL)
        Gtk.main_quit()


FixedFunctionCairoGL()