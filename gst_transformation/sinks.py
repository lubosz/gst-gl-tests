from gi.repository import GLib
from gi.repository import Gtk
from gi.repository import Clutter
from gi.repository import GtkClutter
from gi.repository import ClutterGst
from gi.repository import Gst

from .graphics import *

class PointActor(Clutter.Actor):
  def __init__(self, x, y, w):
    Clutter.Actor.__init__(self)

    self.point = Point(x, y, w)
    
    #self.box = TransformationBox()
    #self.box.init_size(20, 20, 130, 130)
    
    canvas = Clutter.Canvas.new ()
    canvas.set_size (100, 100)

    self.set_content (canvas)
    self.set_size (100, 100)
    
    # connect our drawing code
    canvas.connect ("draw", self.draw)
    
    
    # invalidate the canvas, so that we can draw before the main loop starts
    Clutter.Content.invalidate (canvas)

    # set up a timer that invalidates the canvas every second
    Clutter.threads_add_timeout (GLib.PRIORITY_DEFAULT, 1000, self.invalidate_cb, canvas)

  @staticmethod
  def invalidate_cb (data):
    Clutter.Content.invalidate (data)
    return GLib.SOURCE_CONTINUE

  def draw (self, canvas, cr, width, height):

    self.colors = {
      'white' : Clutter.Color.new(0, 0, 0, 255),
      'blue' : Clutter.Color.new(16, 16, 32, 255),
      'black' : Clutter.Color.new(255, 255, 255, 128),
      'hand' : Clutter.Color.new(16, 32, 16, 196)
    }

    cr.save ()

    # clear the contents of the canvas, to avoid painting
    # over the previous frame
    cr.set_operator (cairo.OPERATOR_CLEAR)
    cr.paint ()
    cr.restore ()

    cr.set_operator (cairo.OPERATOR_OVER)

    # scale the modelview to the size of the surface
    cr.scale (width, height)

    cr.set_line_cap (cairo.LINE_CAP_ROUND)
    cr.set_line_width (0.1)

    # the black rail that holds the seconds indicator
    Clutter.cairo_set_source_color (cr, self.colors['white'])
    cr.translate (0.5, 0.5)
    cr.arc (0, 0, 0.4, 0, pi * 2)
    cr.stroke ()

  
    self.point.draw(cr)
    return True

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
    
    self.video_texture = Clutter.Texture.new()
    self.sink = Gst.ElementFactory.make("cluttersink", None)
    self.sink.props.texture = self.video_texture
    
    self.dragging = False
    self.active_actor = None
    
    if not self.sink:
      print ("Clutter Sink not available.")
      exit()

    self.set_size_request (w, h)

    stage = self.get_stage()
    stage.add_child(self.video_texture)

    #self.rect = Clutter.Rectangle.new_with_color(Clutter.Color.new(255, 0, 0, 128))
    
    #self.rect.set_size(256, 128)
    #self.rect.set_anchor_point(128, 64)
    #self.rect.set_position(256, 256)
    #stage.add_actor(self.rect)
    
    
    
    #point_actor.set_content_scaling_filters (Clutter.ScalingFilter.TRILINEAR,
    #                                   Clutter.ScalingFilter.LINEAR)
    #point_actor = PointActor(50, 50, 100)
    #stage.add_child (point_actor)

    self.transbox = Clutter.Actor.new ()
    self.transbox.set_content (canvas)
    
    self.transbox.set_content_scaling_filters (Clutter.ScalingFilter.TRILINEAR,
                                       Clutter.ScalingFilter.LINEAR)
    stage.add_child (self.transbox)
    """
    """
    
    #self.transbox.set_size(130, 130)
    #self.transbox.set_position(256, 256)
    #self.transbox.set_anchor_point(65,65)

    # bind the size of the actor to that of the stage
    point_actor.add_constraint(Clutter.BindConstraint.new(stage, Clutter.BindCoordinate.SIZE, 0))

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

  def draw (self, canvas, cr, width, height):

  
    cr.save ()

    # clear the contents of the canvas, to avoid painting
    # over the previous frame
    cr.set_operator (cairo.OPERATOR_CLEAR)
    cr.paint ()
    cr.restore ()

    cr.set_operator (cairo.OPERATOR_OVER)

    self.point.draw(cr)
    return True

  def do_expose_event(self, event):
    print("oh hai")
    self.box.init_size(event.area)

  def on_drag_motion(self, stage, event):
    if self.dragging:
      x, y = self.last_position
      self.active_actor.set_position(event.x + x, event.y + y)
      #self.box.transform(event)

  def on_stage_button_release(self, stage, event):
    self.dragging = False
    self.active_actor.clicked = False
    self.active_actor = None

  def on_stage_button_press(self, stage, event):
    #self.box.select_point(event)
    clicked = stage.get_actor_at_pos(Clutter.PickMode.ALL, event.x, event.y);
    if clicked == stage:
      return
    #elif clicked == self.video_texture:
    #  print("video1")
    else:
      x, y = clicked.get_position()
      clicked.clicked = True
      self.last_position = (x - event.x, y - event.y)
      self.dragging = True
      self.active_actor = clicked

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
