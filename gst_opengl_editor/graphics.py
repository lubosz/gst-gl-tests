from gi.repository import Clutter
import cairo
import numpy
from math import pi

from OpenGL.GL import *
from gst_opengl_editor.opengl import *


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
        self.draw_hovered = False

    def init_gl(self, context, canvas_width, canvas_height):
        self.texture = CairoTexture(GL_TEXTURE1, self.width, self.height)
        self.texture.draw(self.draw_cairo)

        self.texture_clicked = CairoTexture(GL_TEXTURE2, self.width, self.height)
        self.draw_clicked = True
        self.draw_hovered = True
        self.texture_clicked.draw(self.draw_cairo)
        self.draw_clicked = False

        self.texture_hovered = CairoTexture(GL_TEXTURE3, self.width, self.height)
        self.draw_hovered = True
        self.texture_hovered.draw(self.draw_cairo)
        self.draw_hovered = False

        self.shader = Shader(context, "simple.vert", "cairo.frag")
        self.mesh = PlaneCairo(canvas_width, canvas_height, self.width, self.height)

    def rebind_texture(self, actor_hovered, actor_clicked):
        if actor_clicked:
            glActiveTexture(GL_TEXTURE2)
            glBindTexture(GL_TEXTURE_RECTANGLE, self.texture_clicked.texture_handle)
            self.shader.shader.set_uniform_1i("cairoSampler", 2)
        elif actor_hovered:
            glActiveTexture(GL_TEXTURE3)
            glBindTexture(GL_TEXTURE_RECTANGLE, self.texture_hovered.texture_handle)
            self.shader.shader.set_uniform_1i("cairoSampler", 3)
        else:
            glActiveTexture(GL_TEXTURE1)
            glBindTexture(GL_TEXTURE_RECTANGLE, self.texture.texture_handle)
            self.shader.shader.set_uniform_1i("cairoSampler", 1)

    def draw_actors(self, actors):
        self.shader.use()
        self.mesh.bind(self.shader)

        for actor in actors:
            self.rebind_texture(actor.hovered, actor.clicked)
            self.shader.set_matrix("mvp", actor.model_matrix())
            self.mesh.draw()

        self.mesh.unbind()

    def draw_cairo(self, cr, w, h):

        x, y, radius = 0.5, 0.5, 0.15
        glow_radius = 1.05
        glow = 0.9

        if self.draw_clicked:
            outer_color = .2
            glow_radius = 1.08
        elif self.draw_hovered:
            outer_color = .8
            glow_radius = 1.08
        else:
            outer_color = .5
            glow_radius = 1.01

        cr.save()
        cr.scale(w, h)
        # clear background
        cr.set_operator(cairo.OPERATOR_OVER)
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.0)
        cr.paint()

        cr.set_source_rgba(glow, glow, glow, 0.9)
        cr.arc(x, y, radius * glow_radius, 0, 2 * pi)
        cr.fill()

        from_point = (x, y - radius)
        to_point = (x, y + radius)
        linear = cairo.LinearGradient(*(from_point + to_point))
        linear.add_color_stop_rgba(0.00, outer_color, outer_color, outer_color, 1)
        linear.add_color_stop_rgba(0.55, .1, .1, .1, 1)
        linear.add_color_stop_rgba(0.65, .1, .1, .1, 1)
        linear.add_color_stop_rgba(1.00, outer_color, outer_color, outer_color, 1)

        cr.set_source(linear)

        cr.arc(x, y, radius * .9, 0, 2 * pi)
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
        self.texture = CairoTexture(GL_TEXTURE4, self.width, self.height)
        self.texture.draw(self.draw_cairo)

        self.shader = Shader(context, "simple.vert", "cairo.frag")
        self.mesh = PlaneCairo(canvas_width, canvas_height, self.width, self.height)

    def rebind_texture(self):
        glActiveTexture(GL_TEXTURE4)
        glBindTexture(GL_TEXTURE_RECTANGLE, self.texture.texture_handle)
        self.shader.shader.set_uniform_1i("cairoSampler", 4)

    def draw(self, handles):
        self.shader.use()
        self.mesh.bind(self.shader)

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

        for handle in self.handle_positions:
            cr.line_to(*self.convert_range(handle))
        cr.line_to(*self.convert_range(self.handle_positions[0]))
        cr.clip()

        cr.set_source_rgba(0.5, 0.5, 0.5, 0.7)

        for handle in self.handle_positions:
            cr.line_to(*self.convert_range(handle))

        cr.line_to(*self.convert_range(self.handle_positions[0]))

        cr.identity_matrix()

        cr.set_line_width(16)
        cr.set_line_join(cairo.LINE_JOIN_BEVEL)

        cr.stroke()

        cr.restore()
