#!/usr/bin/env python3

from gi.repository import Gdk
from gi.repository import Gst
from gi.repository import Gtk
from gi.repository import GdkX11    # for window.get_xid()
from gi.repository import GstVideo  # for sink.set_window_handle()

import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

def window_closed (widget, event, pipeline):
  widget.hide()
  pipeline.set_state(Gst.State.NULL)
  Gtk.main_quit ()

if __name__=="__main__":
  Gdk.init([])
  Gtk.init([])
  Gst.init([])

  pipeline = Gst.Pipeline()
  src = Gst.ElementFactory.make("gltestsrc", None)
  transform = Gst.ElementFactory.make("gltransformation", None)
  sink = Gst.ElementFactory.make("glimagesink", None)

  if not sink or not src:
    print ("GL elements not available.")
    exit()

  pipeline.add(src, transform, sink)
  src.link(transform)
  transform.link(sink)

  window = Gtk.Window()
  window.connect("delete-event", window_closed, pipeline)
  window.set_default_size (1280, 720)
  window.set_title ("Hello OpenGL Sink!")

  drawing_area = Gtk.DrawingArea()
  drawing_area.set_double_buffered (True)
  window.add (drawing_area)

  window.show_all()
  window.realize()
  
  xid = drawing_area.get_window().get_xid()
  sink.set_window_handle (xid)
  
  if pipeline.set_state(Gst.State.PLAYING) == Gst.StateChangeReturn.FAILURE:
    pipeline.set_state(Gst.State.NULL)
  else:
    Gtk.main()
