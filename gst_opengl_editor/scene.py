__author__ = 'Lubosz Sarnecki'

from gi.repository import Graphene
import numpy

from gst_opengl_editor.graphics import *
from gst_opengl_editor.opengl import *


def matrix_to_array(m):
    result = []
    for x in range(0, 4):
        result.append([m.get_value(x, 0),
                       m.get_value(x, 1),
                       m.get_value(x, 2),
                       m.get_value(x, 3)])
    return numpy.array(result, 'd')


class Scene():
    def __init__(self):
        self.meshes = {}
        self.shaders = {}
        self.cairo_textures = {}
        self.actors = {}
        self.graphics = {}
        self.clicked = False
        self.click_point = None
        self.width, self.height = 0, 0
        self.init = False

        self.actors["handle"] = Actor()

    def on_press(self, event):
        self.clicked = True

    def on_motion(self, event):
        if not self.clicked:
            return

        rel_point = (2 * event.x / self.width - 1,
                     -(2 * event.y / self.height - 1))
        self.actors["handle"].position = rel_point

    def on_release(self, event):
        self.clicked = False

    def reshape(self, width, height):
        self.width, self.height = width, height

    def init_gl(self, context, width, height):
        self.width, self.height = width, height

        self.graphics["handle"] = BoxHandleGraphic(100, 100)
        self.graphics["handle"].init_gl(context, width, height)

        self.graphics["video"] = VideoGraphic()
        self.graphics["video"].init_gl(context)

        self.init = True

    def draw(self, context, video_texture):
        if not self.init:
            return

        context.clear_shader()
        glBindTexture(GL_TEXTURE_2D, 0)

        glClearColor(0, 0, 0, 1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        self.graphics["video"].draw(video_texture, numpy.identity(4))
        context.clear_shader()

        self.graphics["handle"].draw_actors(self.actors)

        context.clear_shader()


class Actor():
    def __init__(self):
        self.position = (0, 0)
        self.clicked = False

    def motion(self):
        pass

    def model_matrix(self):
        model_matrix = Graphene.Matrix.alloc()

        translation_vector = Graphene.Point3D.alloc()
        translation_vector.init(self.position[0], self.position[1], 0)

        model_matrix.init_translate(translation_vector)

        return matrix_to_array(model_matrix)


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


class BoxHandleGraphic(Graphic):
    def __init__(self, width, height):
        Graphic.__init__(self)
        self.width, self.height = width, height

    def init_gl(self, context, canvas_width, canvas_height):
        x, y, radius = 0.5, 0.5, 0.5
        p = Point(x, y)
        p.set_width(radius)

        self.texture = CairoTexture(GL_TEXTURE1, self.width, self.height)
        self.texture.draw(p.draw)

        self.texture_clicked = CairoTexture(GL_TEXTURE2, self.width, self.height)
        p.clicked = True
        self.texture_clicked.draw(p.draw)

        self.shader = Shader(context, "simple.vert", "cairo.frag")
        self.mesh = PlaneCairo(canvas_width, canvas_height, self.width, self.height)

    def rebind_click_texture(self, clicked):
        if clicked:
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

        for actor in actors.values():
            self.rebind_click_texture(actor.clicked)
            self.shader.set_matrix("mvp", actor.model_matrix())
            self.mesh.draw()

        self.mesh.unbind()

