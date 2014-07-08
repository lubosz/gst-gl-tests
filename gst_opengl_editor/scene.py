__author__ = 'Lubosz Sarnecki'

from gi.repository import Graphene
import numpy
import math
from gst_opengl_editor.graphics import *


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
        self.handles = {}
        self.graphics = {}
        self.width, self.height = 0, 0
        self.init = False
        self.focused_actor = None

    def on_press(self, event):
        for actor in self.handles.values():
            if actor.is_clicked(self.relative_position(event)):
                self.focused_actor = actor

    def relative_position(self, event):
        # between 0 and 1
        x = event.x / self.width
        y = 1.0 - (event.y / self.height)

        # between -1 and 1
        return (2 * x - 1,
                (2 * y - 1))

    def aspect(self):
        if self.width == 0 or self.height == 0:
            return 1
        return self.width / self.height

    def on_motion(self, sink, event):
        if not self.focused_actor:
            return

        self.focused_actor.position = self.relative_position(event)
        #self.transformation_element.set_property("translation-x", self.aspect * self.scene.actors["handle"].position[0])
        #self.transformation_element.set_property("translation-y", -self.scene.actors["handle"].position[1])

    def on_release(self, sink, event):
        self.focused_actor = None

        for actor in self.handles.values():
            actor.clicked = False

    def reshape(self, sink, context, width, height):
        self.width, self.height = width, height

        if not self.init:
            self.init_gl(context)
            self.init = True

        glViewport(0, 0, width, height)

        return True

    def init_gl(self, context):
        print("OpenGL version: %s" % glGetString(GL_VERSION).decode("utf-8"))
        print("OpenGL vendor: %s" % glGetString(GL_VENDOR).decode("utf-8"))
        print("OpenGL renderer: %s" % glGetString(GL_RENDERER).decode("utf-8"))

        print("Version: %d.%d" % (glGetIntegerv(GL_MAJOR_VERSION),
                                  glGetIntegerv(GL_MINOR_VERSION)))

        glClearColor(0.0, 0.0, 0.0, 0.0)
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glEnable(GL_TEXTURE_RECTANGLE)


class Actor():
    def __init__(self, x=0, y=0):
        self.position = (x, y)
        self.clicked = False
        self.initital_position = self.position

    def motion(self):
        pass

    def is_clicked(self, click):
        vclick = Graphene.Vec2.alloc()
        vclick.init(click[0], click[1])
        vpos = Graphene.Vec2.alloc()
        vpos.init(self.position[0], self.position[1])
        vdistance = vclick.subtract(vpos)

        if vdistance.length() < 0.1:
            self.clicked = True
        else:
            self.clicked = False

        return self.clicked

    def model_matrix(self):
        model_matrix = Graphene.Matrix.alloc()

        translation_vector = Graphene.Point3D.alloc()
        translation_vector.init(self.position[0], self.position[1], 0)

        model_matrix.init_translate(translation_vector)

        return matrix_to_array(model_matrix)


class BoxActor(Actor):
    def __init__(self):
        Actor.__init__(self)
        self.handles = []

    def is_clicked(self, click):
        pass


class TransformScene(Scene):
    def __init__(self):
        Scene.__init__(self)

        self.handles = {
            "1BL": Actor(-1, -1),
            "2TL": Actor(-1, 1),
            "3TR": Actor(1, 1),
            "4BR": Actor(1, -1)}

        self.graphics["handle"] = HandleGraphic(100, 100)
        self.graphics["video"] = VideoGraphic()
        self.graphics["box"] = BoxGraphic(1280, 720, self.handles.values())

    def init_gl(self, context):
        Scene.init_gl(self, context)

        self.graphics["handle"].init_gl(context, self.width, self.height)
        self.graphics["box"].init_gl(context, self.width, self.height)
        self.graphics["video"].init_gl(context)

        self.init = True

    def reposition(self, matrix):
        for handle in self.handles.values():
            vector = numpy.array([handle.initital_position[0] * math.pi,
                                  -handle.initital_position[1],
                                  0, 1])
            vector_transformed = numpy.dot(vector, matrix)

            handle.position = (vector_transformed[0] / self.aspect(),
                               -vector_transformed[1])

    def draw(self, sink, context, video_texture, w, h):
        if not self.init:
            return

        context.clear_shader()

        glClearColor(0, 0, 0, 1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        self.graphics["video"].draw(video_texture, numpy.identity(4))
        context.clear_shader()

        self.graphics["box"].draw(self.handles)
        self.graphics["handle"].draw_actors(self.handles.values())

        return True