from gi.repository import GLib
from gi.repository import Gtk
from gi.repository import Clutter
from gi.repository import GtkClutter
from gi.repository import ClutterGst
from gi.repository import Gst

from .graphics import *

class ClutterSink(GtkClutter.Embed):
  def __init__(self, w, h):
    GtkClutter.init([])
    Clutter.init([])
    ClutterGst.init([])
    GtkClutter.Embed.__init__(self)
    
    self.sink = Gst.ElementFactory.make("cluttersink", None)
    if not self.sink:
      print ("Clutter Sink not available.")
      exit()

    video_texture = Clutter.Texture.new()
    self.sink.props.texture = video_texture

    self.set_size_request (w, h)

    stage = self.get_stage()
    stage.add_child(video_texture)
    
    canvas = Clutter.Canvas.new ()
    canvas.set_size (w, h)

    self.box = TransformationBox(canvas, 0, 0, w, h)
    
    self.box.set_content_scaling_filters (Clutter.ScalingFilter.TRILINEAR,
                                       Clutter.ScalingFilter.LINEAR)
    stage.add_child (self.box)
    
    # bind the size of the actor to that of the stage
    self.box.add_constraint(Clutter.BindConstraint.new(stage, Clutter.BindCoordinate.SIZE, 0))

    # invalidate the canvas, so that we can draw before the main loop starts
    Clutter.Content.invalidate (canvas)

    # set up a timer that invalidates the canvas every second
    Clutter.threads_add_timeout (GLib.PRIORITY_DEFAULT, 10, self.invalidate_cb, canvas)
    
    stage.connect("button-press-event", self.on_stage_button_press)
    stage.connect("button-release-event", self.on_stage_button_release)
    stage.connect("motion-event", self.on_motion)

  def set_transformation_element(self, element):
    self.transformation_element = element

  @staticmethod
  def invalidate_cb (data):
    Clutter.Content.invalidate (data)
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
    self.set_size_request (w, h)
    self.set_double_buffered (True)
    
  def xid(self):
    return self.get_window().get_xid()
    
  def set_handle(self):
    self.sink.set_window_handle(self.xid())
