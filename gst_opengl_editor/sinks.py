from gi.repository import GLib
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Clutter
from gi.repository import GtkClutter
from gi.repository import ClutterGst
from gi.repository import Gst, GstGL

from gst_opengl_editor.graphics import *
from gst_opengl_editor.opengl import Mesh

import numpy, math

class ClutterSink(GtkClutter.Embed):
    def __init__(self, w, h):
        GtkClutter.init([])
        Clutter.init([])
        ClutterGst.init([])
        GtkClutter.Embed.__init__(self)

        self.sink = Gst.ElementFactory.make("cluttersink", None)
        if not self.sink:
            print("Clutter Sink not available.")
            exit()

        video_texture = Clutter.Texture.new()
        self.sink.props.texture = video_texture

        self.set_size_request(w, h)

        stage = self.get_stage()
        stage.add_child(video_texture)

        canvas = Clutter.Canvas.new()
        canvas.set_size(w, h)

        self.box = TransformationBox(canvas, 0, 0, w, h)

        self.box.set_content_scaling_filters(Clutter.ScalingFilter.TRILINEAR,
                                             Clutter.ScalingFilter.LINEAR)
        stage.add_child(self.box)

        # bind the size of the actor to that of the stage
        self.box.add_constraint(Clutter.BindConstraint.new(stage, Clutter.BindCoordinate.SIZE, 0))

        # invalidate the canvas, so that we can draw before the main loop starts
        Clutter.Content.invalidate(canvas)

        # set up a timer that invalidates the canvas every second
        Clutter.threads_add_timeout(GLib.PRIORITY_DEFAULT, 10, self.invalidate_cb, canvas)

        stage.connect("button-press-event", self.on_stage_button_press)
        stage.connect("button-release-event", self.on_stage_button_release)
        stage.connect("motion-event", self.on_motion)

    def set_transformation_element(self, element):
        self.transformation_element = element
        self.box.transformation_properties = element

    @staticmethod
    def invalidate_cb(data):
        Clutter.Content.invalidate(data)
        return GLib.SOURCE_CONTINUE

    def on_motion(self, stage, event):
        self.box.motion(event)

    def on_stage_button_release(self, stage, event):
        self.box.button_release()

    def on_stage_button_press(self, stage, event):
        self.box.button_press(event)

    def set_handle(self):
        pass

from OpenGL.GL import *


class CairoTexture():
    def __init__(self, gl_id, width, height):
        self.width, self.height = width, height
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        self.ctx = cairo.Context(self.surface)
        glActiveTexture(gl_id)
        self.texture_handle = glGenTextures(1)

    def draw(self, callback):
        glBindTexture(GL_TEXTURE_RECTANGLE, self.texture_handle)
        callback(self.ctx, self.width, self.height)
        glTexImage2D(GL_TEXTURE_RECTANGLE,
                     0,
                     GL_RGBA,
                     self.width,
                     self.height,
                     0,
                     GL_BGRA,
                     GL_UNSIGNED_BYTE,
                     self.surface.get_data())
        glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_DECAL)

    def delete(self):
        if self.texture_handle:
            glDeleteTextures(self.texture_handle)


class GstOverlaySink(Gtk.DrawingArea):
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

    def __init__(self, name, w, h):
        Gtk.DrawingArea.__init__(self)
        from gi.repository import GdkX11, GstVideo

        self.sink = Gst.ElementFactory.make(name, None)
        self.set_size_request(w, h)
        self.set_double_buffered(True)

        self.sink.connect("client-draw", self.draw)
        self.sink.connect("client-reshape", self.reshape)

        self.connect("button-press-event", self.on_button_press)
        self.connect("button-release-event", self.on_button_release)
        self.connect("motion-notify-event", self.on_motion)

        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.add_events(Gdk.EventMask.BUTTON_RELEASE_MASK)
        self.add_events(Gdk.EventMask.POINTER_MOTION_MASK)

        #from IPython import embed
        #embed()

        self.gl_init = False
        self.meshes = {}
        self.shaders = {}
        self.cairo_textures = {}

    def xid(self):
        return self.get_window().get_xid()

    def set_handle(self):
        self.sink.set_window_handle(self.xid())

    def set_transformation_element(self, element):
        self.transformation_element = element

    def on_button_press(self, sink, event):
        print("press", event.x, event.y)

    def on_button_release(self, sink, event):
        print("release", event.x, event.y)

    def on_motion(self, sink, event):
        print("motion", event.x, event.y)

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

        #width, height = 100, 100

        self.meshes["plane_wh"].add(
            "uv", [
                0.0, 0.0,
                width, 0.0,
                width, height,
                0.0, height], 2)
        self.meshes["plane_wh"].set_index([0, 1, 3, 2])

        for shader in self.shaders.values():
            if not shader.compile():
                exit()

    def reshape(self, sink, context, width, height):

        if not self.gl_init:
            self.init_gl(context, width, height)
            self.gl_init = True

        glViewport(0, 0, width, height)

        self.aspect = width/height

        x, y, radius = 0.5, 0.5, 0.5

        p = Point(x, y)
        p.set_width(radius)

        self.cairo_textures["handle"] = CairoTexture(GL_TEXTURE1, 100, 100)
        self.cairo_textures["handle"].draw(p.draw)

        self.cairo_textures["handle_clicked"] = CairoTexture(GL_TEXTURE2, 100, 100)
        p.clicked = True
        self.cairo_textures["handle_clicked"].draw(p.draw)

        return True

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

        glBindTexture(GL_TEXTURE_RECTANGLE, self.cairo_textures["handle"].texture_handle)
        self.shaders["cairo"].set_uniform_1i("cairoSampler", 1)

        location = glGetUniformLocation(self.shaders["cairo"].get_program_handle(), "mvp")
        glUniformMatrix4fv(location, 1, GL_FALSE, numpy.identity(4))

        self.meshes["plane_wh"].draw()
        self.meshes["plane_wh"].unbind()

        context.clear_shader()

    def draw(self, sink, context, texture, width, height):
        if len(self.shaders) < 1:
            return

        if len(self.cairo_textures) < 1:
            return

        self.draw_two_pass(context, texture)

        return True