#!/usr/bin/env python3

videouri = "file:///home/bmonkey/workspace/ges/data/hd/sintel_trailer-720p.ogv"

from gi.repository import Gdk, Gst, Gtk, GdkX11, GstVideo

import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

def pad_added_cb(element, stuff, sink):
    print(element, stuff, sink)
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

def quit(window):
  window.hide()
  pipeline.set_state(Gst.State.NULL)
  Gtk.main_quit ()

def window_closed (widget, event, pipeline):
  quit(widget)

def key_pressed (widget, key):
  if key.keyval == Gdk.KEY_Escape:
    quit(widget)

class Video(Gtk.DrawingArea): 
  def __init__(self, w, h):
    Gtk.DrawingArea.__init__(self)
    self.set_size_request (w, h)
    self.set_double_buffered (True)
    
  def xid(self):
    return self.get_window().get_xid()

if __name__=="__main__":
  Gdk.init([])
  Gtk.init([])
  Gst.init([])

  pipeline = Gst.Pipeline()
  src = Gst.ElementFactory.make("uridecodebin", None)
  src.set_property("uri", videouri)
  sink = Gst.ElementFactory.make("glimagesink", None)
  
  src.connect("pad-added", pad_added_cb, sink)

  if not sink or not src:
    print ("GL elements not available.")
    exit()

  pipeline.add(src, sink)
  #src.link(sink)
  
  bus = pipeline.get_bus()
  bus.add_signal_watch()
  bus.connect("message", bus_cb)

  window = Gtk.Window()
  window.connect("delete-event", window_closed, pipeline)
  window.connect("key-press-event", key_pressed)
  window.set_title ("Load a video file")

  video = Video(1280, 720)
  window.add(video)
  window.show_all()
  window.realize()
  
  sink.set_window_handle(video.xid())
  
  if pipeline.set_state(Gst.State.PLAYING) == Gst.StateChangeReturn.FAILURE:
    pipeline.set_state(Gst.State.NULL)
  else:
    Gtk.main()
  
