#!/usr/bin/python

from gi.repository import Gdk
from gi.repository import ClutterGst
from gi.repository import Clutter
from gi.repository import GtkClutter
from gi.repository import Gst
from gi.repository import Gtk

import IPython

def on_drag_motion(stage, event):
  #IPython.embed()
  print ("oh hai", event.x, event.y)

def on_stage_button_release(stage, event):
  print ("oh hai", event.x, event.y)

def on_stage_button_press(stage, event):
  #IPython.embed()

  #find which actor was clicked
  clicked = stage.get_actor_at_pos(Clutter.PickMode.ALL, event.x, event.y);

  #ignore clicks on the stage
  if (clicked == stage):
    return

  #hide the actor that was clicked
  clicked.hide()


class TransformationLine(Clutter.Actor):
     #def __init__(self, coords, startPoint=None, endPoint=None):
     def __init__(self):
         Clutter.Actor.__init__(self)
         #self.coords = coords

         self.canvas = Clutter.Canvas()
         self.canvas.set_size(320, 240)
         self.canvas.connect("draw", self._drawCb)
         self.set_content(self.canvas)
         self.set_reactive(True)

         self.gotDragged = False

         self.dragAction = Clutter.DragAction()
         self.add_action(self.dragAction)

         #self.dragAction.connect("drag-begin", self._dragBeginCb)
         #self.dragAction.connect("drag-end", self._dragEndCb)
         #self.dragAction.connect("drag-progress", self._dragProgressCb)

         #self.connect("button-release-event", self._clickedCb)
         #self.connect("motion-event", self._motionEventCb)
         #self.connect("enter-event", self._enterEventCb)
         #self.connect("leave-event", self._leaveEventCb)

         #self.startPoint = startPoint
         #self.endPoint = endPoint

     def _drawCb(self, canvas, cr, width, unused_height):
         """
         This is where we actually create the line segments for keyframe curves.
         We draw multiple lines (one-third of the height each) to add a "shadow"
         around the actual line segment to improve visibility.
         """
         
         print("oh hai")
         
         cr.set_operator(cairo.OPERATOR_CLEAR)
         cr.paint()
         cr.set_operator(cairo.OPERATOR_OVER)

         _max_height = 3

         cr.set_source_rgba(0, 0, 0, 0.5)
         cr.move_to(0, _max_height / 3)
         cr.line_to(width, _max_height / 3)
         cr.set_line_width(_max_height / 3)
         cr.stroke()



# only ClutterGst needs to be initialized to run the example correctly
Gdk.init([])
Gtk.init([])
GtkClutter.init([])
Gst.init([])
Clutter.init([])
ClutterGst.init([])

# changing "x" to "" fixes the crash
label = Gtk.Label("x")

window = Gtk.Window()
vbox = Gtk.VBox()
window.add(vbox)

texture = Clutter.Texture.new()
sink = Gst.ElementFactory.make("cluttersink", None)
sink.props.texture = texture
src = Gst.ElementFactory.make ("gltestsrc", None)
trans = Gst.ElementFactory.make ("gltransformation", None)
pipeline = Gst.Pipeline()
pipeline.add(src)
pipeline.add(trans)
pipeline.add(sink)
src.link(trans)
trans.link(sink)

src.set_property("pattern", 1)
trans.set_property("rotation-z", 45.0)

embed = GtkClutter.Embed()
embed.set_size_request(320, 240)

line = TransformationLine()

stage = embed.get_stage()
stage.add_child(texture)

stage.add_child(line)

rect = Clutter.Rectangle.new_with_color(Clutter.Color.new(255, 0, 0, 128))
rect.set_size(256, 128)
rect.set_anchor_point(128, 64)
rect.set_position(256, 256)
stage.add_actor(rect)

stage.set_size(320, 240)
stage.show_all()

line.show()

vbox.pack_start(embed, True, True, 0)
vbox.pack_start(label, False, False, 0)

stage.connect("button-press-event", on_stage_button_press)
stage.connect("button-release-event", on_stage_button_release)
stage.connect("motion-event", on_drag_motion)
window.connect("delete-event", Gtk.main_quit)

window.show_all()

pipeline.set_state(Gst.State.PLAYING)

Gtk.main()

