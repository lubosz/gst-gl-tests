#!/usr/bin/env python3
from math import pi, sin, cos, ceil
from gi.repository import GLib, Clutter
import cairo

class ClockExample():

  idle_resize_id = 0

  def __init__ (self):
    # initialize Clutter
    Clutter.init([])
    
    self.colors = {
      'white' : Clutter.Color.new(0, 0, 0, 255),
      'blue' : Clutter.Color.new(16, 16, 32, 255),
      'black' : Clutter.Color.new(255, 255, 255, 128),
      'hand' : Clutter.Color.new(16, 32, 16, 196)
    }

    # create a resizable stage
    stage = Clutter.Stage.new ()
    stage.set_title ("2D Clock")
    stage.set_user_resizable (True)
    stage.set_background_color (self.colors['blue'])
    stage.set_size (300, 300)
    stage.show ()

    # our 2D canvas, courtesy of Cairo
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
    actor.connect ("allocation-changed", self.on_actor_resize)

    # quit on destroy
    stage.connect ("destroy", self.on_destroy)

    # connect our drawing code
    canvas.connect ("draw", self.draw_clock)

    # invalidate the canvas, so that we can draw before the main loop starts
    Clutter.Content.invalidate (canvas)

    # set up a timer that invalidates the canvas every second
    Clutter.threads_add_timeout (GLib.PRIORITY_DEFAULT, 1000, self.invalidate_clock, canvas)

    Clutter.main ()

  def draw_clock (self, canvas, cr, width, height):
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

  @staticmethod
  def invalidate_clock (data):
    Clutter.Content.invalidate (data)
    return GLib.SOURCE_CONTINUE

  def idle_resize (self, actor):
    #match the canvas size to the actor's
    width, height = actor.get_size ()
    actor.set_size (ceil (width), ceil (height))

    # unset the guard
    self.idle_resize_id = 0

    # remove the timeout
    return GLib.SOURCE_REMOVE

  def on_actor_resize (self, actor, allocation, flags):
    # throttle multiple actor allocations to one canvas resize we use a guard
    # variable to avoid queueing multiple resize operations
    if self.idle_resize_id == 0:
      self.idle_resize_id = Clutter.threads_add_timeout(GLib.PRIORITY_DEFAULT, 
                                                        1000, self.idle_resize, actor)

  @staticmethod
  def on_destroy(stage):
    Clutter.main_quit()


ClockExample()
