#!/usr/bin/python

from gi.repository import Gdk
from gi.repository import ClutterGst
from gi.repository import Clutter
from gi.repository import GtkClutter
from gi.repository import Gst
from gi.repository import Gtk

def on_stage_button_release(stage, event):
  print ("oh hai", event.x, event.y)

def on_stage_button_press(stage, event):
  #find which actor was clicked
  clicked = stage.get_actor_at_pos(Clutter.PickMode.ALL, event.x, event.y);

  #ignore clicks on the stage
  if (clicked == stage):
    return

  #hide the actor that was clicked
  clicked.hide()

Gdk.init([])
Gtk.init([])
GtkClutter.init([])
Gst.init([])
Clutter.init([])
ClutterGst.init([])

window = Gtk.Window()

texture = Clutter.Texture.new()
sink = Gst.ElementFactory.make("cluttersink", None)
sink.props.texture = texture
src = Gst.ElementFactory.make ("videotestsrc", None)
pipeline = Gst.Pipeline()
pipeline.add(src, sink)
src.link(sink)

embed = GtkClutter.Embed()
embed.set_size_request(320, 240)

stage = embed.get_stage()
stage.add_child(texture)

rect = Clutter.Rectangle.new_with_color(Clutter.Color.new(255, 0, 0, 128))
rect.set_size(256, 128)
rect.set_anchor_point(128, 64)
rect.set_position(256, 256)
stage.add_actor(rect)

stage.set_size(320, 240)
stage.show_all()

window.add(embed)

stage.connect("button-press-event", on_stage_button_press)
stage.connect("button-release-event", on_stage_button_release)
window.connect("delete-event", Gtk.main_quit)

window.show_all()

pipeline.set_state(Gst.State.PLAYING)

Gtk.main()

