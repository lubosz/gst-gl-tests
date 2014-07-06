#!/usr/bin/env python3

from gi.repository import Gst, Gtk, GdkX11, GstVideo, GstGL

from OpenGL.GL import *

import numpy
import signal
import cairo
import math

signal.signal(signal.SIGINT, signal.SIG_DFL)

from IPython import embed

class ShaderGLSink():
    vertex_src = """
      attribute vec4 position;
      attribute vec2 uv;
      uniform mat4 mvp;
      varying vec2 out_uv;
      void main()
      {
         gl_Position = mvp * position;
         out_uv = uv;
      }
    """

    fragment_src = """
      varying vec2 out_uv;
      uniform sampler2DRect cairoSampler;
      uniform sampler2D videoSampler;
      void main()
      {
        vec4 video = texture2D (videoSampler, out_uv);
        vec4 cairo = texture2DRect (cairoSampler, out_uv * vec2(1280, 720));
        gl_FragColor = video * cairo;
        //gl_FragColor = cairo;
      }
    """

    def reshape(self, sink, context, width, height):
        glEnable(GL_TEXTURE_RECTANGLE)

        self.shader = GstGL.GLShader.new(context)
        self.shader.set_fragment_source(self.fragment_src)
        self.shader.set_vertex_source(self.vertex_src)
        if not self.shader.compile():
            exit()

        glViewport(0, 0, width, height)

        self.aspect = width/height
        
        # cairo
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        self.ctx = cairo.Context(surface)
        self.ctx.scale(width, height)

        glActiveTexture(GL_TEXTURE1)
        if self.cairo_texture_id:
            glDeleteTextures(1, self.cairo_texture_id)
        self.cairo_texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_RECTANGLE, self.cairo_texture_id)
        self.render_cairo(self.ctx, width, height)
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

        if not self.shader:
            return

        if not self.cairo_texture_id:
            return

        positions = numpy.array([-1, 1.0, 0.0, 1.0,
                                 1, 1.0, 0.0, 1.0,
                                 1, -1.0, 0.0, 1.0,
                                 -1, -1.0, 0.0, 1.0])

        uvs = numpy.array([0.0, 0.0,
                           1, 0.0,
                           1, 1,
                           0.0, 1])

        indices = [0, 1, 2, 3, 0]

        context.clear_shader()
        #glBindTexture(GL_TEXTURE_2D, 0)
        #glBindTexture(GL_TEXTURE_RECTANGLE, 0)

        glClearColor(0, 0, 0, 1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        self.shader.use()

        position_loc = self.shader.get_attribute_location("position")

        uv_loc = self.shader.get_attribute_location("uv")

        # Load the vertex position
        glVertexAttribPointer(position_loc, 4, GL_FLOAT, GL_FALSE, 0, positions)

        # Load the texture coordinate
        glVertexAttribPointer(uv_loc, 2, GL_FLOAT, GL_FALSE, 0, uvs)

        glEnableVertexAttribArray(position_loc)
        glEnableVertexAttribArray(uv_loc)

        #glDeleteTextures(texture)
        #glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, texture)
        self.shader.set_uniform_1i("videoSampler", 0)

        glBindTexture(GL_TEXTURE_RECTANGLE, self.cairo_texture_id)
        self.shader.set_uniform_1i("cairoSampler", 1)

        location = glGetUniformLocation(self.shader.get_program_handle(), "mvp")

        glUniformMatrix4fv(location, 1, GL_FALSE, numpy.identity(4))

        glDrawElements(GL_TRIANGLE_STRIP, 5, GL_UNSIGNED_SHORT, indices)

        glDisableVertexAttribArray(position_loc)
        glDisableVertexAttribArray(uv_loc)

        context.clear_shader()

        return True

    @staticmethod
    def window_closed(widget, event, pipeline):
        widget.hide()
        pipeline.set_state(Gst.State.NULL)
        Gtk.main_quit()

    @staticmethod
    def render_cairo(cr, width, height):
        cr.save()

        # clear background
        cr.set_operator(cairo.OPERATOR_OVER)
        #cr.scale(width, height)
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
        cr.arc(0.2, 0.1, 0.1, -math.pi/2, 0)
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

    def __init__(self):
        Gtk.init([])
        Gst.init([])

        width, height = 1280, 720
        self.aspect = width/height

        self.cairo_texture_id = None

        pipeline = Gst.Pipeline()
        src = Gst.ElementFactory.make("videotestsrc", None)
        sink = Gst.ElementFactory.make("glimagesink", None)

        if not sink or not src:
            print("GL elements not available.")
            exit()

        self.shader = None

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
        drawing_area.set_double_buffered(True)
        window.add(drawing_area)

        window.show_all()

        xid = drawing_area.get_window().get_xid()
        sink.set_window_handle(xid)
        
        if pipeline.set_state(Gst.State.PLAYING) == Gst.StateChangeReturn.FAILURE:
            pipeline.set_state(Gst.State.NULL)
        else:
            Gtk.main()


ShaderGLSink()
