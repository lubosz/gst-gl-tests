from gi.repository import Gtk
from gst_opengl_editor.scene import matrix_to_array


class Slider(Gtk.Box):
    def __init__(self, sliderbox, property, min, max, step, init):
        Gtk.Box.__init__(self)

        self.init = init

        label = Gtk.Label(property)
        self.scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, min, max, step)

        self.scale.set_property("expand", True)
        self.scale.set_value(init)
        self.scale.add_mark(init, Gtk.PositionType.RIGHT)
        self.scale.connect("value-changed", sliderbox.value_changed, property)

        self.set_orientation(Gtk.Orientation.HORIZONTAL)

        self.add(label)
        self.add(self.scale)

        self.name = property

    def get(self):
        return self.scale.get_value()

    def set(self, value):
        self.scale.set_value(value)

    def reset(self):
        self.scale.set_value(self.init)


class SliderBox(Gtk.Box):

    sliders = {}

    def __init__(self, element, setup):
        Gtk.Box.__init__(self)

        for name in sorted(setup):
            slider = Slider(self, name, *setup[name])
            self.sliders[name] = slider
            self.add(slider)

        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_size_request(300, 300)

        image = Gtk.Image.new_from_stock("gtk-clear", Gtk.IconSize.BUTTON)
        button = Gtk.Button()
        button.set_image(image)
        button.connect("clicked", self.reset_values)

        self.add(button)

        self.element = element

    def reset_values(self, button):
        for slider in self.sliders.values():
            slider.reset()


class Transformation2DSliderBox(SliderBox):
    def value_changed(self, scale, property):
        self.element.set_property(property, scale.get_value())
        self.scene.reposition()

    def __init__(self, element, scene):
        setup = {
            "rotation-z": (-720, 720, 1, 0),
            "translation-x": (-5, 5, 0.01, 0),
            "translation-y": (-5, 5, 0.01, 0),
            "scale-x": (0, 4, 0.1, 1),
            "scale-y": (0, 4, 0.1, 1)
        }
        SliderBox.__init__(self, element, setup)

        self.scene = scene

    def mvp(self):
        return matrix_to_array(self.element.get_property("mvp-matrix"))


class Transformation3DSliderBox(SliderBox):
    def value_changed(self, scale, property):
        self.element.set_property(property, scale.get_value())

    @staticmethod
    def check_cb(check, element):
        element.set_property("ortho", check.get_active())

    def __init__(self, element):

        self.sliders = [
            Slider(self, "rotation-x", -720, 720, 1, 0),
            Slider(self, "rotation-y", -720, 720, 1, 0),
            Slider(self, "rotation-z", -720, 720, 1, 0),
            Slider(self, "translation-x", -5, 5, 0.01, 0),
            Slider(self, "translation-y", -5, 5, 0.01, 0),
            Slider(self, "translation-z", -5, 5, 0.01, 0),
            Slider(self, "scale-x", 0, 4, 0.1, 1),
            Slider(self, "scale-y", 0, 4, 0.1, 1),
            Slider(self, "fov", 0, 180, 0.5, 90)]

        check = Gtk.CheckButton.new_with_label("Orthographic Projection")
        check.connect("toggled", self.check_cb, element)
        self.add(check)

        SliderBox.__init__(self, element)
