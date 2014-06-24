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
    
    self.colors = {
      'white' : Clutter.Color.new(0, 0, 0, 255),
      'blue' : Clutter.Color.new(16, 16, 32, 255),
      'black' : Clutter.Color.new(255, 255, 255, 128),
      'hand' : Clutter.Color.new(16, 32, 16, 196)
    }
    
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

    #self.rect = Clutter.Rectangle.new_with_color(Clutter.Color.new(255, 0, 0, 128))
    
    #self.rect.set_size(256, 128)
    #self.rect.set_anchor_point(128, 64)
    #self.rect.set_position(256, 256)
    #stage.add_actor(self.rect)
    
    self.point = Point(100, 100)
    
    self.box = TransformationBox()
    self.box.init_size(20, 20, 130, 130)
    
    canvas = Clutter.Canvas.new ()
    canvas.set_size (w, h)

    self.transbox = Clutter.Actor.new ()
    self.transbox.set_content (canvas)
    
    self.transbox.set_content_scaling_filters (Clutter.ScalingFilter.TRILINEAR,
                                       Clutter.ScalingFilter.LINEAR)
    stage.add_child (self.transbox)
    
    #self.transbox.set_size(130, 130)
    #self.transbox.set_position(256, 256)
    #self.transbox.set_anchor_point(65,65)

    # bind the size of the actor to that of the stage
    self.transbox.add_constraint(Clutter.BindConstraint.new(stage, Clutter.BindCoordinate.SIZE, 0))

    # resize the canvas whenever the actor changes size
    #actor.connect ("allocation-changed", self.on_actor_resize)

    # connect our drawing code
    canvas.connect ("draw", self.draw)
    
    
    # invalidate the canvas, so that we can draw before the main loop starts
    Clutter.Content.invalidate (canvas)

    # set up a timer that invalidates the canvas every second
    Clutter.threads_add_timeout (GLib.PRIORITY_DEFAULT, 1000, self.invalidate_cb, canvas)
    
    stage.connect("button-press-event", self.on_stage_button_press)
    stage.connect("button-release-event", self.on_stage_button_release)
    stage.connect("motion-event", self.on_drag_motion)
    #self.connect("draw", self.do_expose_event)

  def do_expose_event(self, event):
    print("oh hai")
    self.box.init_size(event.area)

  @staticmethod
  def invalidate_cb (data):
    Clutter.Content.invalidate (data)
    return GLib.SOURCE_CONTINUE

  def draw (self, canvas, cr, width, height):
    self.box.draw(cr)
    return True

  def on_drag_motion(self, stage, event):
    if self.dragging:
      x, y = self.last_position
      self.transbox.set_position(event.x + x, event.y + y)
      #self.box.transform(event)

  def on_stage_button_release(self, stage, event):
    self.dragging = False

  def on_stage_button_press(self, stage, event):
    self.box.select_point(event)
    clicked = stage.get_actor_at_pos(Clutter.PickMode.ALL, event.x, event.y);
    if clicked == stage:
      return
    #elif clicked == self.rect:
    else:
      x, y = self.transbox.get_position()
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
