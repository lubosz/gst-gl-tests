from gi.repository import Gtk, Graphene
import numpy
from gst_opengl_editor.scene import matrix_to_array


class Slider(Gtk.Box):
    def __init__(self, sliderbox, property, min, max, step, init):
        Gtk.Box.__init__(self)

        label = Gtk.Label(property)
        scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, min, max, step)

        scale.set_property("expand", True)
        scale.set_value(init)
        scale.connect("value-changed", sliderbox.value_changed, property)

        self.set_orientation(Gtk.Orientation.HORIZONTAL)

        self.add(label)
        self.add(scale)


class Transformation2DSliderBox(Gtk.Box):
    def value_changed(self, scale, property):
        self.element.set_property(property, scale.get_value())
        self.scene.reposition(self.build_mvp())

    def __init__(self, element, scene):
        Gtk.Box.__init__(self)

        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.add(Slider(self, "rotation-z", -720, 720, 1, 0))

        self.add(Slider(self, "translation-x", -5, 5, 0.01, 0))
        self.add(Slider(self, "translation-y", -5, 5, 0.01, 0))

        self.add(Slider(self, "scale-x", 0, 4, 0.1, 1))
        self.add(Slider(self, "scale-y", 0, 4, 0.1, 1))

        self.set_size_request(300, 300)

        self.element = element
        self.scene = scene

    def zrotation(self):
        return self.element.get_property("rotation-z")

    def xtranslation(self):
        return self.element.get_property("translation-x")

    def ytranslation(self):
        return self.element.get_property("translation-y")

    def xscale(self):
        return self.element.get_property("scale-x")

    def yscale(self):
        return self.element.get_property("scale-y")

    def build_model(self):
        model_matrix = Graphene.Matrix.alloc()
        model_matrix.init_scale(self.xscale(), self.yscale(), 1.0)
        model_matrix.rotate(self.zrotation(), Graphene.vec3_z_axis())

        translation_vector = Graphene.Point3D.alloc()
        translation_vector.init(self.xtranslation(), self.ytranslation(), 0)
        model_matrix.translate(translation_vector)

        return matrix_to_array(model_matrix)

    def build_projection(self):
        projection_matrix = Graphene.Matrix.alloc()
        projection_matrix.init_perspective(90.0, self.scene.aspect(), 0.1, 100.0)
        return matrix_to_array(projection_matrix)

    @staticmethod
    def build_view():
        eye = Graphene.Vec3.alloc()
        eye.init(0, 0, 1)
        center = Graphene.Vec3.alloc()
        center.init(0, 0, 0)
        up = Graphene.Vec3.alloc()
        up.init(0, 1, 0)
        view_matrix = Graphene.Matrix.alloc()
        view_matrix.init_look_at(eye, center, up)
        return matrix_to_array(view_matrix)

    def build_mvp(self):
        model = self.build_model()
        projection = self.build_projection()
        view = self.build_view()

        vp = numpy.dot(view, projection)
        mvp = numpy.dot(vp, model)

        return mvp


class Transformation3DSliderBox(Gtk.Box):
    def value_changed(self, scale, property):
        self.element.set_property(property, scale.get_value())

    @staticmethod
    def check_cb(check, element):
        element.set_property("ortho", check.get_active())

    def __init__(self, element):
        Gtk.Box.__init__(self)

        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.add(Slider(self, "rotation-x", -720, 720, 1, 0))
        self.add(Slider(self, "rotation-y", -720, 720, 1, 0))
        self.add(Slider(self, "rotation-z", -720, 720, 1, 0))

        self.add(Slider(self, "translation-x", -5, 5, 0.01, 0))
        self.add(Slider(self, "translation-y", -5, 5, 0.01, 0))
        self.add(Slider(self, "translation-z", -5, 5, 0.01, 0))

        self.add(Slider(self, "scale-x", 0, 4, 0.1, 1))
        self.add(Slider(self, "scale-y", 0, 4, 0.1, 1))

        self.add(Slider(self, "fovy", 0, 180, 0.5, 90))
        check = Gtk.CheckButton.new_with_label("Orthographic Projection")
        check.connect("toggled", self.check_cb, element)
        self.add(check)
        self.set_size_request(300, 300)

        self.element = element