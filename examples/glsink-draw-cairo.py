#!/usr/bin/env python3

from gi.repository import Gst, Gtk, GdkX11, GstVideo, GstGL

from OpenGL.GL import *

import numpy
import signal
import cairo
import math

signal.signal(signal.SIGINT, signal.SIG_DFL)


class Mesh():
    def __init__(self, type):
        self.type = type
        self.buffers = {}
        self.locations = {}
        self.element_sizes = {}

    def add(self, name, buffer, element_size):
        self.buffers[name] = buffer
        self.element_sizes[name] = element_size

    def set_index(self, index):
        self.index = index

    def bind(self, shader):
        for name in self.buffers:
            self.locations[name] = shader.get_attribute_location(name)
            glVertexAttribPointer(
                self.locations[name],
                self.element_sizes[name],
                GL_FLOAT, GL_FALSE, 0,
                self.buffers[name])
            glEnableVertexAttribArray(self.locations[name])

    def draw(self):
        glDrawElements(self.type,
                       len(self.index),
                       GL_UNSIGNED_SHORT,
                       self.index)

    def unbind(self):
        for name in self.buffers:
            glDisableVertexAttribArray(self.locations[name])


class ShaderGLSink():
    simple_vert = """
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

    video_cairo_frag = """
       varying vec2 out_uv;
       uniform sampler2DRect cairoSampler;
       uniform sampler2D videoSampler;
       void main()
       {
        vec4 video = texture2D (videoSampler, out_uv);
        vec4 cairo = texture2DRect (cairoSampler, out_uv * vec2(1280, 720));
        gl_FragColor = video - cairo + vec4(out_uv, 0, 1);
       }
     """

    video_frag = """
      varying vec2 out_uv;
      uniform sampler2D videoSampler;
      void main()
      {
        gl_FragColor = texture2D (videoSampler, out_uv);
      }
    """

    cairo_frag = """
      varying vec2 out_uv;
      uniform sampler2DRect cairoSampler;
      void main()
      {
        gl_FragColor = texture2DRect (cairoSampler, out_uv);
      }
    """

    def __init__(self):
        Gtk.init([])
        Gst.init([])

        width, height = 1280, 720
        self.aspect = width/height

        self.gl_init = False

        self.meshes = {}

        self.cairo_texture_id = None

        pipeline = Gst.Pipeline()
        src = Gst.ElementFactory.make("videotestsrc", None)
        sink = Gst.ElementFactory.make("glimagesink", None)

        if not sink or not src:
            print("GL elements not available.")
            exit()

        self.shaders = {}

        caps = Gst.Caps.from_string("video/x-raw, width=%d, height=%d" % (width, height))
        cf = Gst.ElementFactory.make("capsfilter")
        cf.set_property("caps", caps)

        pipeline.add(src, cf, sink)

        src.link(cf)
        cf.link(sink)

        window = Gtk.Window()
        window.connect("delete-event", self.window_closed, pipeline)
        window.set_default_size(width, height)
        window.set_title("Hello Cairo, OpenGL and GLSink!")

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

    def init_gl(self, context, width, height):
        print("OpenGL version: %s" % glGetString(GL_VERSION).decode("utf-8"))
        print("OpenGL vendor: %s" % glGetString(GL_VENDOR).decode("utf-8"))
        print("OpenGL renderer: %s" % glGetString(GL_RENDERER).decode("utf-8"))

        print("Version: %d.%d" % (glGetIntegerv(GL_MAJOR_VERSION),
              glGetIntegerv(GL_MINOR_VERSION)))

        glClearColor(0.0, 0.0, 0.0, 0.0)
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glEnable(GL_TEXTURE_RECTANGLE)

        self.shaders["video"] = GstGL.GLShader.new(context)
        self.shaders["video"].set_vertex_source(self.simple_vert)
        self.shaders["video"].set_fragment_source(self.video_frag)

        self.shaders["cairo"] = GstGL.GLShader.new(context)
        self.shaders["cairo"].set_vertex_source(self.simple_vert)
        self.shaders["cairo"].set_fragment_source(self.cairo_frag)

        self.shaders["videocairo"] = GstGL.GLShader.new(context)
        self.shaders["videocairo"].set_vertex_source(self.simple_vert)
        self.shaders["videocairo"].set_fragment_source(self.video_cairo_frag)

        self.meshes["plane_tri"] = Mesh(GL_TRIANGLE_STRIP)
        self.meshes["plane_tri"].add(
            "position", [
                -1, 1, 0, 1,
                1, 1, 0, 1,
                1, -1, 0, 1,
                -1, -1, 0, 1], 4)
        self.meshes["plane_tri"].add(
            "uv", [
                0.0, 0.0,
                1.0, 0.0,
                1.0, 1.0,
                0.0, 1.0], 2)
        self.meshes["plane_tri"].set_index([0, 1, 3, 2])

        self.meshes["plane_wh"] = Mesh(GL_TRIANGLE_STRIP)
        self.meshes["plane_wh"].add(
            "position", [
                -1, 1, 0, 1,
                1, 1, 0, 1,
                1, -1, 0, 1,
                -1, -1, 0, 1], 4)
        self.meshes["plane_wh"].add(
            "uv", [
                0.0, 0.0,
                width, 0.0,
                width, height,
                0.0, height], 2)
        self.meshes["plane_wh"].set_index([0, 1, 3, 2])

        self.meshes["plane_quad"] = Mesh(GL_QUADS)
        self.meshes["plane_quad"].add(
            "position", [
                1.0,  1.0,  0.0, 1,
                -1.0,  1.0,  0.0, 1,
                -1.0, -1.0,  0.0, 1,
                1.0, -1.0,  0.0, 1], 4)
        self.meshes["plane_quad"].add(
            "uv", [
                1.0, 0.0,
                0.0, 0.0,
                0.0, 1.0,
                1.0, 1.0], 2)
        self.meshes["plane_quad"].set_index([0, 1, 2, 3])

        for shader in self.shaders.values():
            if not shader.compile():
                exit()

    def reshape(self, sink, context, width, height):

        if not self.gl_init:
            self.init_gl(context, width, height)
            self.gl_init = True

        glViewport(0, 0, width, height)

        self.aspect = width/height
        
        # cairo
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        self.ctx = cairo.Context(surface)
        self.ctx.scale(width, height)

        glActiveTexture(GL_TEXTURE1)
        if self.cairo_texture_id:
            glDeleteTextures(self.cairo_texture_id)
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

    def draw_one_pass(self, context, texture):
        context.clear_shader()

        glClearColor(0, 0, 0, 1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        self.shaders["videocairo"].use()

        self.meshes["plane_quad"].bind(self.shaders["videocairo"])

        glBindTexture(GL_TEXTURE_RECTANGLE, self.cairo_texture_id)
        self.shaders["videocairo"].set_uniform_1i("cairoSampler", 1)

        glBindTexture(GL_TEXTURE_2D, texture)
        self.shaders["videocairo"].set_uniform_1i("videoSampler", 0)

        location = glGetUniformLocation(self.shaders["videocairo"].get_program_handle(), "mvp")

        glUniformMatrix4fv(location, 1, GL_FALSE, numpy.identity(4))

        self.meshes["plane_quad"].draw()
        self.meshes["plane_quad"].unbind()

    def draw_two_pass(self, context, texture):
        # video pass
        context.clear_shader()
        glBindTexture(GL_TEXTURE_2D, 0)

        glClearColor(0, 0, 0, 1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        self.shaders["video"].use()
        self.meshes["plane_tri"].bind(self.shaders["video"])

        glBindTexture(GL_TEXTURE_2D, texture)
        self.shaders["video"].set_uniform_1i("videoSampler", 0)

        location = glGetUniformLocation(self.shaders["video"].get_program_handle(), "mvp")
        glUniformMatrix4fv(location, 1, GL_FALSE, numpy.identity(4))

        self.meshes["plane_tri"].draw()
        self.meshes["plane_tri"].unbind()

        context.clear_shader()

        # cairo pass
        self.shaders["cairo"].use()
        self.meshes["plane_wh"].bind(self.shaders["cairo"])

        glBindTexture(GL_TEXTURE_RECTANGLE, self.cairo_texture_id)
        self.shaders["cairo"].set_uniform_1i("cairoSampler", 1)

        location = glGetUniformLocation(self.shaders["cairo"].get_program_handle(), "mvp")
        glUniformMatrix4fv(location, 1, GL_FALSE, numpy.identity(4))

        self.meshes["plane_wh"].draw()
        self.meshes["plane_wh"].unbind()

        context.clear_shader()

    def draw(self, sink, context, texture, width, height):
        if len(self.shaders) < 1:
            return

        if not self.cairo_texture_id:
            return

        self.draw_two_pass(context, texture)
        #self.draw_one_pass(context, texture)

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
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.0)
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


ShaderGLSink()
