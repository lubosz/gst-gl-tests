#!/usr/bin/python

from gi.repository import Gdk
from gi.repository import ClutterGst
from gi.repository import Clutter
from gi.repository import GtkClutter
from gi.repository import Gst
from gi.repository import Gtk

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

stage.set_size(320, 240)
stage.show_all()

window.add(embed)
window.connect("delete-event", Gtk.main_quit)

window.show_all()

pipeline.set_state(Gst.State.PLAYING)

Gtk.main()

