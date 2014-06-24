from gi.repository import GLib
from gi.repository import Gtk
from gi.repository import Clutter
from gi.repository import GtkClutter
from gi.repository import ClutterGst
from gi.repository import Gst

from math import pi, sin, cos, ceil

import cairo

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

    self.rect = Clutter.Rectangle.new_with_color(Clutter.Color.new(255, 0, 0, 128))
    
    self.rect.set_size(256, 128)
    self.rect.set_anchor_point(128, 64)
    self.rect.set_position(256, 256)
    stage.add_actor(self.rect)
    
    canvas = Clutter.Canvas.new ()
    canvas.set_size (300, 300)

    actor = Clutter.Actor.new ()
    actor.set_content (canvas)
    
    actor.set_content_scaling_filters (Clutter.ScalingFilter.TRILINEAR,
                                       Clutter.ScalingFilter.LINEAR)
    stage.add_child (actor)

    # bind the size of the actor to that of the stage
    actor.add_constraint(Clutter.BindConstraint.new(stage, Clutter.BindCoordinate.SIZE, 0))

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

  @staticmethod
  def invalidate_cb (data):
    Clutter.Content.invalidate (data)
    return GLib.SOURCE_CONTINUE

  def draw (self, canvas, cr, width, height):
    now = GLib.DateTime.new_now_local ()
    seconds = GLib.DateTime.get_second (now) * pi / 30
    minutes = GLib.DateTime.get_minute (now) * pi / 30
    hours = GLib.DateTime.get_hour (now) * pi / 6

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

    # the seconds indicator
    Clutter.cairo_set_source_color (cr, self.colors['black'])
    cr.move_to (0, 0)
    cr.arc (sin (seconds) * 0.4, - cos (seconds) * 0.4, 0.05, 0, pi * 2)
    cr.fill ()

    # the minutes hand
    Clutter.cairo_set_source_color (cr, self.colors['hand'])
    cr.move_to (0, 0)
    cr.line_to (sin (minutes) * 0.4, -cos (minutes) * 0.4)
    cr.stroke ()

    # the hours hand
    cr.move_to (0, 0)
    cr.line_to (sin (hours) * 0.2, -cos (hours) * 0.2)
    cr.stroke ()

    # we're done drawing
    return True


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
    #elif clicked == self.rect:
    else:
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
