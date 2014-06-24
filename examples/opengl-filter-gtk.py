#!/usr/bin/env python3

from gi.repository import Gdk, GdkX11, Gst, Gtk, GstVideo

import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

def pad_added_cb(element, stuff, sink):
    element.link(sink)

def bus_cb(bus, message):
    if message.type == Gst.MessageType.EOS:
        print("eos")
        Gtk.main_quit()
    elif message.type == Gst.MessageType.ERROR:
        print (message.parse_error())
        Gtk.main_quit()
    else:
        pass

def property_cb(scale, element, property):
  element.set_property(property, scale.get_value())

def check_cb(check, element):
  element.set_property("ortho", check.get_active())

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

class TransformationBox(Gtk.Box):
  def __init__(self):
    Gtk.Box.__init__(self)
    self.set_orientation(Gtk.Orientation.VERTICAL)
    self.add(ElementScale(transform, "rotation-x", -720, 720, 1, 0))
    self.add(ElementScale(transform, "rotation-y", -720, 720, 1, 0))
    self.add(ElementScale(transform, "rotation-z", -720, 720, 1, 0))

    self.add(ElementScale(transform, "translation-x", -5, 5, 0.01, 0))
    self.add(ElementScale(transform, "translation-y", -5, 5, 0.01, 0))
    self.add(ElementScale(transform, "translation-z", -5, 5, 0.01, 0))

    self.add(ElementScale(transform, "scale-x", 0, 4, 0.1, 1))
    self.add(ElementScale(transform, "scale-y", 0, 4, 0.1, 1))
    
    self.add(ElementScale(transform, "fovy", 0, 180, 0.5, 90))
    check = Gtk.CheckButton.new_with_label("Orthographic Projection")
    check.connect("toggled", check_cb, transform)
    self.add(check)
    self.set_size_request(300, 300)

class GstOverlaySink(Gtk.DrawingArea): 
  def __init__(self, name, w, h):
    Gtk.DrawingArea.__init__(self)
    self.sink = Gst.ElementFactory.make(name, None)
    self.set_size_request (w, h)
    self.set_double_buffered (True)
    
  def xid(self):
    return self.get_window().get_xid()
    
  def set_handle(self):
    self.sink.set_window_handle(self.xid())

if __name__=="__main__":
  Gdk.init([])
  Gtk.init([])
  Gst.init([])

  pipeline = Gst.Pipeline()
  src = Gst.ElementFactory.make("videotestsrc", None)
  
  sink = GstOverlaySink("glimagesink", 1280, 720)
  
  transform = Gst.ElementFactory.make("gltransformation", None)
  pipeline.add(src, transform, sink.sink)
  src.link(transform)
  src.connect("pad-added", pad_added_cb, transform)
  transform.link(sink.sink)

  bus = pipeline.get_bus()
  bus.add_signal_watch()
  bus.connect("message", bus_cb)

  window = Gtk.Window()
  window.connect("delete-event", window_closed, pipeline)
  window.connect("key-press-event", key_pressed)
  window.set_title ("OpenGL Transformation")

  box = Gtk.Box()
  box.set_orientation(Gtk.Orientation.HORIZONTAL)

  box.add(sink)
  
  box.add(TransformationBox())

  window.add(box)
  window.show_all()
  window.realize()
  
  sink.set_handle()
  
  if pipeline.set_state(Gst.State.PLAYING) == Gst.StateChangeReturn.FAILURE:
    pipeline.set_state(Gst.State.NULL)
  else:
    Gtk.main()
