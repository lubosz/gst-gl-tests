#!/usr/bin/env python3

from gi.repository import Gdk, Gtk, Gst

import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

class GstOverlaySink(Gtk.DrawingArea):
    def __init__(self, name, w, h):
        Gtk.DrawingArea.__init__(self)
        from gi.repository import GdkX11, GstVideo

        self.sink = Gst.ElementFactory.make(name, None)
        self.set_size_request(w, h)
        #self.sink.handle_events (False)
        #self.sink.handle_events (True)
        
        self.add_events(Gdk.EventMask.POINTER_MOTION_MASK)
        
        self.connect("motion-notify-event", self.on_motion)
        
    def on_motion(self, sink, event):
        print(event.x, event.y)
        
    def xid(self):
        return self.get_window().get_xid()

    def set_handle(self):
        self.sink.set_window_handle(self.xid())


def quit_app(widget):
    widget.hide()
    Gtk.main_quit()


def window_closed(widget, event):
    quit_app(widget)


def key_pressed(widget, key):
    if key.keyval == Gdk.KEY_Escape:
        quit_app(widget)

Gtk.init([])
Gst.init([])

window = Gtk.Window()
window.connect("delete-event", window_closed)
window.set_default_size(640, 480)
window.set_title("Foo")

pipeline = Gst.Pipeline()
src = Gst.ElementFactory.make("gltestsrc", None)
sink = GstOverlaySink("glimagesink", 640, 480)
#sink = GstOverlaySink("xvimagesink", 640, 480)

pipeline.add(src, sink.sink)
src.link(sink.sink)

window.add(sink)
window.show_all()

sink.set_handle()

if pipeline.set_state(Gst.State.PLAYING) == Gst.StateChangeReturn.FAILURE:
    pipeline.set_state(Gst.State.NULL)
else:
    Gtk.main()
