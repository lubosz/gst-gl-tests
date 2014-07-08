from gi.repository import GLib
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Clutter
from gi.repository import GtkClutter
from gi.repository import ClutterGst
from gi.repository import Gst, GstGL, Graphene

from gst_opengl_editor.graphics import *
from gst_opengl_editor.opengl import *

import numpy
from OpenGL.GL import *
from gst_opengl_editor.scene import Actor, Scene, FreeTransformScene


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


class GstOverlaySink(Gtk.DrawingArea):
    def __init__(self, name, w, h):
        Gtk.DrawingArea.__init__(self)
        from gi.repository import GdkX11, GstVideo

        self.sink = Gst.ElementFactory.make(name, None)
        self.set_size_request(w, h)
        self.set_double_buffered(True)

    def xid(self):
        return self.get_window().get_xid()

    def set_handle(self):
        self.sink.set_window_handle(self.xid())


class CairoGLSink(GstOverlaySink):
    def __init__(self, w, h):
        GstOverlaySink.__init__(self, "glimagesink", w, h)

        self.sink.connect("client-draw", self.draw)
        self.sink.connect("client-reshape", self.reshape)

        self.connect("button-press-event", self.on_button_press)
        self.connect("button-release-event", self.on_button_release)
        self.connect("motion-notify-event", self.on_motion)

        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.add_events(Gdk.EventMask.BUTTON_RELEASE_MASK)
        self.add_events(Gdk.EventMask.POINTER_MOTION_MASK)

        self.gl_init = False

        self.scene = FreeTransformScene()

        self.canvas_width, self.canvas_height = w, h
        self.aspect = w/h

        self.transformation_element = None
        self.pipeline = None
        self.pipeline_position = 0

    def set_transformation_element(self, element):
        self.transformation_element = element

    def set_pipeline(self, pipeline):
        self.pipeline = pipeline

    def set_pipeline_position(self, position):
        self.pipeline_position = position

    def flush_seek(self):
        self.pipeline.seek_simple(
            Gst.Format.TIME,
            Gst.SeekFlags.FLUSH,
            #3 * Gst.SECOND)
            self.pipeline_position)
        return True

    def on_button_press(self, sink, event):
        self.scene.on_press(event)

        if self.pipeline.get_state(Gst.CLOCK_TIME_NONE)[1] == Gst.State.PAUSED:
            GLib.timeout_add(90, self.flush_seek)

    def on_button_release(self, sink, event):
        self.scene.on_release(event)

    def on_motion(self, sink, event):
        self.scene.on_motion(event)

        #self.transformation_element.set_property("translation-x", self.aspect * self.scene.actors["handle"].position[0])
        #self.transformation_element.set_property("translation-y", -self.scene.actors["handle"].position[1])

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

        self.scene.init_gl(context, width, height)

    def reshape(self, sink, context, width, height):
        if not self.gl_init:
            self.init_gl(context, width, height)
            self.gl_init = True

        glViewport(0, 0, width, height)

        self.aspect = width/height
        self.scene.reshape(width, height)

        return True

    def draw(self, sink, context, video_texture, width, height):
        self.scene.draw(context, video_texture)

        return True