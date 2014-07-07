from gi.repository import Gtk


def property_cb(scale, element, property):
    element.set_property(property, scale.get_value())


def check_cb(check, element):
    element.set_property("ortho", check.get_active())


class ElementScale(Gtk.Box):
    def __init__(self, element, property, min, max, step, init):
        Gtk.Box.__init__(self)

        label = Gtk.Label(property)
        scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, min, max, step)

        scale.set_property("expand", True)
        scale.set_value(init)
        scale.connect("value-changed", property_cb, element, property)

        self.set_orientation(Gtk.Orientation.HORIZONTAL)

        self.add(label)
        self.add(scale)


class ElementScaleBox(Gtk.Box):
    def __init__(self, element):
        Gtk.Box.__init__(self)
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.add(ElementScale(element, "rotation-x", -720, 720, 1, 0))
        self.add(ElementScale(element, "rotation-y", -720, 720, 1, 0))
        self.add(ElementScale(element, "rotation-z", -720, 720, 1, 0))

        self.add(ElementScale(element, "translation-x", -5, 5, 0.01, 0))
        self.add(ElementScale(element, "translation-y", -5, 5, 0.01, 0))
        self.add(ElementScale(element, "translation-z", -5, 5, 0.01, 0))

        self.add(ElementScale(element, "scale-x", 0, 4, 0.1, 1))
        self.add(ElementScale(element, "scale-y", 0, 4, 0.1, 1))

        self.add(ElementScale(element, "fovy", 0, 180, 0.5, 90))
        check = Gtk.CheckButton.new_with_label("Orthographic Projection")
        check.connect("toggled", check_cb, element)
        self.add(check)
        self.set_size_request(300, 300)
