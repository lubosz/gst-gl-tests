#!/usr/bin/env python3

from gi.repository import Gdk
from gi.repository import Gst
from gi.repository import Gtk
from gi.repository import GdkX11    # for window.get_xid()
from gi.repository import GstVideo  # for sink.set_window_handle()

from OpenGL.GL import *

import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

def reshapeCallback (sink, width, height):
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    #gluPerspective(45, (gfloat)width/(gfloat)height, 0.1, 100);
    #glOrtho(0.0f, width, height, 0.0f, 0.0f, 1.0f);
    glMatrixMode(GL_MODELVIEW)

    return True

def drawCallback(sink, texture, width, height):
    glEnable (GL_TEXTURE_2D)
    glBindTexture (GL_TEXTURE_2D, texture)
    glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    glTexEnvi (GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()


    glBegin(GL_QUADS)
    glTexCoord2f(1.0, 0.0)
    glVertex3f(-1.0, -1.0,  0.0)
    glTexCoord2f(0.0, 0.0)
    glVertex3f( 1.0, -1.0,  0.0)
    glTexCoord2f(0.0, 1.0)
    glVertex3f( 1.0,  1.0,  0.0)
    glTexCoord2f(1.0, 1.0)
    glVertex3f(-1.0,  1.0,  0.0)
    glEnd()
    
    glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
    glBindTexture(GL_TEXTURE_2D, 0)

    glLineWidth(40)

    glBegin(GL_QUADS)
    glColor4f(0.8, 0.0, 0.8, 0.5)
    glVertex3f(-0.5, -0.5,  0.0)
    glVertex3f( 0.5, -0.5,  0.0)
    glVertex3f( 0.5,  0.5,  0.0)
    glVertex3f(-0.5,  0.5,  0.0)
    glEnd()
    
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

    return True

def window_closed (widget, event, pipeline):
  widget.hide()
  pipeline.set_state(Gst.State.NULL)
  Gtk.main_quit ()

if __name__=="__main__":
  Gdk.init([])
  Gtk.init([])
  Gst.init([])

  pipeline = Gst.Pipeline()
  src = Gst.ElementFactory.make("videotestsrc", None)
  trans = Gst.ElementFactory.make("gltransformation", None)
  sink = Gst.ElementFactory.make("glimagesink", None)

  if not sink or not src:
    print ("GL elements not available.")
    exit()

  pipeline.add(src, trans, sink)
  src.link(trans)
  trans.link(sink)

  window = Gtk.Window()
  window.connect("delete-event", window_closed, pipeline)
  window.set_default_size (1280, 720)
  window.set_title ("Hello OpenGL Sink!")
  
  sink.connect("client-draw", drawCallback)
  sink.connect("client-reshape", reshapeCallback)
  
  trans.set_property("rotation-z", 45.0)

  drawing_area = Gtk.DrawingArea()
  drawing_area.set_double_buffered (True)
  window.add (drawing_area)

  window.show_all()
  window.realize()
  
  xid = drawing_area.get_window().get_xid()
  sink.set_window_handle (xid)
  
  if pipeline.set_state(Gst.State.PLAYING) == Gst.StateChangeReturn.FAILURE:
    pipeline.set_state(Gst.State.NULL)
  else:
    Gtk.main()
