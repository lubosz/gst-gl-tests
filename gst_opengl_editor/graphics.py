from gi.repository import Clutter
import cairo

from math import pi

from OpenGL.GL import *
from gst_opengl_editor.opengl import *

def hex_to_rgb(value):
    return tuple(float(int(value[i:i + 2], 16)) / 255.0 for i in range(0, 6, 2))


class Graphic():
    def __init__(self):
        self.texture = None
        self.texture_clicked = None
        self.shader = None
        self.mesh = None


class VideoGraphic(Graphic):
    def __init__(self):
        Graphic.__init__(self)

    def init_gl(self, context):
        self.shader = Shader(context, "simple.vert", "video.frag")
        self.mesh = PlaneTriangleFan()

    def draw(self, video_texture, matrix):
        self.shader.use()
        self.mesh.bind(self.shader)

        glBindTexture(GL_TEXTURE_2D, video_texture)
        self.shader.shader.set_uniform_1i("videoSampler", 0)

        self.shader.set_matrix("mvp", matrix)

        self.mesh.draw()
        self.mesh.unbind()


class HandleGraphic(Graphic):
    def __init__(self, width, height):
        Graphic.__init__(self)
        self.draw_clicked = False
        self.width, self.height = width, height
        self.color = hex_to_rgb('49a0e0')
        self.clickedColor = hex_to_rgb('ff8b1b')

    def init_gl(self, context, canvas_width, canvas_height):
        self.texture = CairoTexture(GL_TEXTURE1, self.width, self.height)
        self.texture.draw(self.draw_cairo)

        self.texture_clicked = CairoTexture(GL_TEXTURE2, self.width, self.height)
        self.draw_clicked = True
        self.texture_clicked.draw(self.draw_cairo)
        self.draw_clicked = False

        self.shader = Shader(context, "simple.vert", "cairo.frag")
        self.mesh = PlaneCairo(canvas_width, canvas_height, self.width, self.height)

    def rebind_texture(self, actor_clicked):
        if actor_clicked:
            glActiveTexture(GL_TEXTURE2)
            glBindTexture(GL_TEXTURE_RECTANGLE, self.texture_clicked.texture_handle)
            self.shader.shader.set_uniform_1i("cairoSampler", 2)
        else:
            glActiveTexture(GL_TEXTURE1)
            glBindTexture(GL_TEXTURE_RECTANGLE, self.texture.texture_handle)
            self.shader.shader.set_uniform_1i("cairoSampler", 1)

    def draw_actors(self, actors):
        self.shader.use()
        self.mesh.bind(self.shader)

        for actor in actors:
            self.rebind_texture(actor.clicked)
            self.shader.set_matrix("mvp", actor.model_matrix())
            self.mesh.draw()

        self.mesh.unbind()

    def draw_cairo(self, cr, w, h):

        x, y, radius = 0.5, 0.5, 0.25

        cr.save()
        cr.scale(w, h)
        # clear background
        cr.set_operator(cairo.OPERATOR_OVER)
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.0)
        cr.paint()

        from_point = (x, y - radius)
        to_point = (x, y + radius)

        linear = cairo.LinearGradient(*(from_point + to_point))

        linear.add_color_stop_rgba(0.00, .6, .6, .6, .5)
        linear.add_color_stop_rgba(0.50, .4, .4, .4, .1)
        linear.add_color_stop_rgba(0.60, .4, .4, .4, .1)
        linear.add_color_stop_rgba(1.00, .6, .6, .6, .5)

        # x, y, radius
        inner_circle = (x + .1, y - .1, radius / 10.0)
        outer_circle = (x, y, radius)

        radial = cairo.RadialGradient(*(inner_circle + outer_circle))
        if self.draw_clicked:
            radial.add_color_stop_rgb(0.0, *self.clickedColor)
        else:
            radial.add_color_stop_rgb(0, *self.color)
        radial.add_color_stop_rgb(1, 0.1, 0.1, 0.1)

        glow_multiplier = 1.5

        inner_circle = (x, y, radius * .9)
        outer_circle = (x, y, radius * glow_multiplier)

        radial_glow = cairo.RadialGradient(*(inner_circle+outer_circle))
        radial_glow.add_color_stop_rgba(0, 0.9, 0.9, 0.9, 1)
        radial_glow.add_color_stop_rgba(1, 0.9, 0.9, 0.9, 0)

        cr.set_source(radial_glow)
        cr.arc(x, y, radius * glow_multiplier, 0, 2 * pi)
        cr.fill()

        cr.arc(x, y, radius * .9, 0, 2 * pi)
        cr.set_source(radial)
        cr.fill()

        cr.arc(x, y, radius * .9, 0, 2 * pi)
        cr.set_source(linear)
        cr.fill()

        cr.restore()


class BoxGraphic(Graphic):
    def __init__(self, width, height, handles):
        Graphic.__init__(self)
        self.width, self.height = width, height
        self.handle_positions = []
        for handle in handles:
            self.handle_positions.append(handle.position)

    def init_gl(self, context, canvas_width, canvas_height):
        self.texture = CairoTexture(GL_TEXTURE3, self.width, self.height)
        self.texture.draw(self.draw_cairo)

        self.shader = Shader(context, "simple.vert", "cairo.frag")
        self.mesh = PlaneCairo(canvas_width, canvas_height, self.width, self.height)

    def rebind_texture(self):
        glActiveTexture(GL_TEXTURE3)
        glBindTexture(GL_TEXTURE_RECTANGLE, self.texture.texture_handle)
        self.shader.shader.set_uniform_1i("cairoSampler", 3)

    def draw(self, handles):
        self.shader.use()
        self.mesh.bind(self.shader)

        import numpy

        self.handle_positions = []

        for h in sorted(handles):
            self.handle_positions.append(handles[h].position)
        self.texture.draw(self.draw_cairo)

        self.rebind_texture()
        self.shader.set_matrix("mvp", numpy.identity(4))
        self.mesh.draw()

        self.mesh.unbind()

    def convert_range(self, pos):
        return ((pos[0] + 1) / 2.0,
                (-pos[1] + 1) / 2.0)

    def draw_cairo(self, cr, w, h):
        cr.save()
        cr.scale(w, h)

        # clear background
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.0)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()

        cr.set_source_rgba(0.5, 0.5, 0.5, 0.7)

        # from [-1, 1] to [0, 1]
        for handle in self.handle_positions:
            cr.line_to(*self.convert_range(handle))

        cr.line_to(*self.convert_range(self.handle_positions[0]))

        cr.identity_matrix()

        cr.set_line_width(32)
        cr.set_line_join(cairo.LINE_JOIN_BEVEL)

        cr.stroke()

        cr.restore()