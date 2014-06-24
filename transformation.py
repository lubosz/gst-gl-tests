#!/usr/bin/env python3

videouri = "file:///home/bmonkey/workspace/ges/data/hd/Return to split point.mp4"

from IPython import embed

#from gi.repository import Gdk, Gst, Gtk, GdkX11, GstVideo


from gi.repository import Gdk
from gi.repository import GdkX11
from gi.repository import ClutterGst
from gi.repository import Clutter
from gi.repository import GtkClutter
from gi.repository import Gst
from gi.repository import Gtk

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

class ClutterSink(GtkClutter.Embed):
  def __init__(self, w, h):
    GtkClutter.init([])
    Clutter.init([])
    ClutterGst.init([])
    
    GtkClutter.Embed.__init__(self)
    
    texture = Clutter.Texture.new()
    self.sink = Gst.ElementFactory.make("cluttersink", None)
    self.sink.props.texture = texture
    
    self.dragging = False
    
    if not self.sink:
      print ("Clutter Sink not available.")
      exit()

    self.set_size_request (w, h)

    stage = self.get_stage()
    stage.add_child(texture)

    self.rect = Clutter.Rectangle.new_with_color(Clutter.Color.new(255, 0, 0, 128))
    
    embed()
    
    self.rect.set_size(256, 128)
    self.rect.set_anchor_point(128, 64)
    self.rect.set_position(256, 256)
    stage.add_actor(self.rect)
    
    stage.connect("button-press-event", self.on_stage_button_press)
    stage.connect("button-release-event", self.on_stage_button_release)
    stage.connect("motion-event", self.on_drag_motion)

  def on_drag_motion(self, stage, event):
    if self.dragging:
      x, y = self.last_position
      self.rect.set_position(event.x + x, event.y + y)

  def on_stage_button_release(self, stage, event):
    self.dragging = False

  def on_stage_button_press(self, stage, event):
    clicked = stage.get_actor_at_pos(Clutter.PickMode.ALL, event.x, event.y);
    if clicked == stage:
      return
    elif clicked == self.rect:
      x, y = self.rect.get_position()
      self.last_position = (x - event.x, y - event.y)
      self.dragging = True

  def set_handle(self):
    pass

class GstOverlaySink(Gtk.DrawingArea): 
  def __init__(self, name, w, h):
    Gtk.DrawingArea.__init__(self)
    from gi.repository import GdkX11, GstVideo
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
  #src = Gst.ElementFactory.make("gltestsrc", None)
  #src = Gst.ElementFactory.make("videotestsrc", None)
  
  src = Gst.ElementFactory.make("uridecodebin", None)
  src.set_property("uri", videouri)

  sink = ClutterSink(1280, 720)
  #sink = GstOverlaySink("glimagesink", 1280, 720)
  
  transform = False
  #transform = True

  if transform:
    transform = Gst.ElementFactory.make("gltransformation", None)
    #transform = Gst.ElementFactory.make("glmosaic", None)
    pipeline.add(src, transform, sink.sink)
    src.link(transform)
    src.connect("pad-added", pad_added_cb, transform)
    transform.link(sink.sink)
  else:
    pipeline.add(src, sink.sink)
    src.link(sink.sink)
    src.connect("pad-added", pad_added_cb, sink.sink)

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
  
  if transform:
    box.add(TransformationBox())

  window.add(box)
  window.show_all()
  window.realize()
  
  sink.set_handle()
  
  if pipeline.set_state(Gst.State.PLAYING) == Gst.StateChangeReturn.FAILURE:
    pipeline.set_state(Gst.State.NULL)
  else:
    Gtk.main()
