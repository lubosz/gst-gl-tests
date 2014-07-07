#!/usr/bin/env python3

from gi.repository import Gdk, Gtk

import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)


def press(x, y):
    print(x, y)


def quit_app(widget):
    widget.hide()
    Gtk.main_quit()


def window_closed(widget, event):
    quit_app(widget)


def key_pressed(widget, key):
    if key.keyval == Gdk.KEY_Escape:
        quit_app(widget)


window = Gtk.Window()
window.connect("delete-event", window_closed)
window.connect("key-press-event", key_pressed)
window.set_default_size(100, 100)
window.set_title("Foo")

drawing_area = Gtk.DrawingArea()

#from IPython import embed
#embed()

drawing_area.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
drawing_area.connect("button-press-event", press)

window.add(drawing_area)
window.show_all()

Gtk.main()