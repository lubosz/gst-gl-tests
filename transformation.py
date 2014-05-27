#!/usr/bin/env python3

from IPython import embed

from gi.repository import Gdk, Gst, Gtk, GdkX11, GstVideo

import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

def property_cb(scale, element, property):
  element.set_property(property, scale.get_value())

def quit(window):
  window.hide()
  pipeline.set_state(Gst.State.NULL)
  Gtk.main_quit ()

def window_closed (widget, event, pipeline):
  quit(widget)

def key_pressed (widget, key):
  if key.keyval == Gdk.KEY_Escape:
    quit(widget)

class ElementScale(Gtk.Box):
  def __init__(self, element, property, min, max, step, init):
    Gtk.Box.__init__(self)

    label = Gtk.Label(property)
    scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, min, max, step)
    
    scale.set_property("expand", True)
    scale.set_value(init)
    scale.connect("value-changed", property_cb, element, property)
    
    self.set_orientation(Gtk.Orientation.HORIZONTAL)
    
    self.add(label)
    self.add(scale)

class Video(Gtk.DrawingArea): 
  def __init__(self, w, h):
    Gtk.DrawingArea.__init__(self)
    self.set_size_request (w, h)
    self.set_double_buffered (True)
    
  def xid(self):
    return self.get_window().get_xid()

if __name__=="__main__":
  Gdk.init([])
  Gtk.init([])
  Gst.init([])

  pipeline = Gst.Pipeline()
  src = Gst.ElementFactory.make("gltestsrc", None)
  transform = Gst.ElementFactory.make("gltransformation", None)
  #sink = Gst.ElementFactory.make("fpsdisplaysink", None)
  sink = Gst.ElementFactory.make("glimagesink", None)

  if not sink or not src:
    print ("GL elements not available.")
    exit()

  pipeline.add(src, transform, sink)
  src.link(transform)
  transform.link(sink)

  window = Gtk.Window()
  window.connect("delete-event", window_closed, pipeline)
  window.connect("key-press-event", key_pressed)
  #window.set_default_size (1280, 720)
  window.set_title ("OpenGL Transformation")

  box = Gtk.Box()
  box.set_orientation(Gtk.Orientation.VERTICAL)
  
  video = Video(1280, 720)
  box.add(video)

  #box.add(LabelScale("Rotation", 0, 360, 1, 0, red_cb, sink))
  #box.add(LabelScale("X", -100, 100, 1, 0, red_cb, sink))
  #box.add(LabelScale("Y", -100, 100, 1, 0, red_cb, sink))
  #box.add(LabelScale("Scale", 0, 50, 1, 1, red_cb, sink))
  
  box.add(ElementScale(transform, "red", 0, 1, 0.005, 0))
  box.add(ElementScale(transform, "green", 0, 1, 0.005, 0))
  box.add(ElementScale(transform, "blue", 0, 1, 0.005, 0))
  box.add(ElementScale(transform, "fovy", 0, 180, 0.5, 45))
  box.add(ElementScale(transform, "aspect", 0, 100, 0.5, 0))
  box.add(ElementScale(transform, "znear", 0, 100, 0.1, 0.1))
  box.add(ElementScale(transform, "zfar", 0, 1000, 5, 100))
  
  window.add(box)

  window.show_all()
  window.realize()
  
  sink.set_window_handle(video.xid())
  
  if pipeline.set_state(Gst.State.PLAYING) == Gst.StateChangeReturn.FAILURE:
    pipeline.set_state(Gst.State.NULL)
  else:
    Gtk.main()
