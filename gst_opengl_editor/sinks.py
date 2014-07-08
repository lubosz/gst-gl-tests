from gi.repository import GLib
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Gst, GstGL, Graphene

from gst_opengl_editor.scene import *

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

        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.add_events(Gdk.EventMask.BUTTON_RELEASE_MASK)
        self.add_events(Gdk.EventMask.POINTER_MOTION_MASK)

        self.gl_init = False

        self.scene = TransformScene()

        self.sink.connect("client-draw", self.scene.draw)
        self.sink.connect("client-reshape", self.scene.reshape)

        self.connect("button-press-event", self.on_button_press)
        self.connect("button-release-event", self.scene.on_release)
        self.connect("motion-notify-event", self.scene.on_motion)

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
