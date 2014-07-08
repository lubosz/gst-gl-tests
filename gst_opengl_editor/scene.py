__author__ = 'Lubosz Sarnecki'

from gi.repository import Graphene
import numpy

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
        self.actors = []
        self.graphics = {}
        self.width, self.height = 0, 0
        self.init = False
        self.focused_actor = None

    def on_press(self, event):
        for actor in self.actors:
            if actor.is_clicked(self.relative_position(event)):
                self.focused_actor = actor

    def relative_position(self, event):
        # between 0 and 1
        x = event.x / self.width
        y = 1.0 - (event.y / self.height)

        # between -1 and 1
        return (2 * x - 1,
                (2 * y - 1))

    def on_motion(self, event):
        if not self.focused_actor:
            return

        self.focused_actor.position = self.relative_position(event)

    def on_release(self, event):
        self.focused_actor = None

        for actor in self.actors:
            actor.clicked = False

    def reshape(self, width, height):
        self.width, self.height = width, height


class Actor():
    def __init__(self, x=0, y=0):
        self.position = (x, y)
        self.clicked = False

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

class FreeTransformScene(Scene):
    def __init__(self):
        Scene.__init__(self)

        self.actors.append(Actor(-1, -1))
        self.actors.append(Actor(-1,  1))
        self.actors.append(Actor( 1,  1))
        self.actors.append(Actor( 1, -1))

        self.graphics["handle"] = BoxHandleGraphic(100, 100)
        self.graphics["video"] = VideoGraphic()
        self.graphics["box"] = BoxGraphic(1280, 720, self.actors)

    def init_gl(self, context, width, height):
        self.width, self.height = width, height

        self.graphics["handle"].init_gl(context, width, height)
        self.graphics["box"].init_gl(context, width, height)
        self.graphics["video"].init_gl(context)

        self.init = True

    def draw(self, context, video_texture):
        if not self.init:
            return

        context.clear_shader()

        glClearColor(0, 0, 0, 1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        self.graphics["video"].draw(video_texture, numpy.identity(4))
        context.clear_shader()

        self.graphics["box"].draw(self.actors)
        self.graphics["handle"].draw_actors(self.actors)