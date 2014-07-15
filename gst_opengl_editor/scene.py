__author__ = 'Lubosz Sarnecki'

from gi.repository import Graphene, Gdk
import numpy
import math
from gst_opengl_editor.graphics import *
from numpy import array


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
        self.box_actor = BoxActor()
        self.dragged = False
        self.selected = False
        self.clicked_outside = False

    def deselect(self):
        self.selected = False
        self.set_cursor(Gdk.CursorType.ARROW) # default

    def on_press(self, event):


        if event.get_button()[1] == 3:
            # Right click
            self.deselect()
        elif event.get_button()[1] == 1:
            # Left click

            self.focused_actor = None
            self.some_button_pressed = True

            for actor in self.handles.values():
                if actor.is_clicked(self.relative_position(event)):
                    self.focused_actor = actor
                    self.click_point = self.relative_position(event)

            if self.box_actor.is_clicked(self.relative_position(event), self.handles):
                self.dragged = True
                self.selected = True

                pos = self.relative_position(event)

                self.oldpos = ((self.slider_box.sliders["translation-x"].get() - pos[0] * self.aspect()),
                               self.slider_box.sliders["translation-y"].get() + pos[1])
            elif self.focused_actor:
                pass
            else:
                #clicked outside of box
                self.clicked_outside = True

                self.oldrot = self.slider_box.sliders["rotation-z"].get() - self.get_rotation(event)


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

    def set_cursor(self, type):
        display = Gdk.Display.get_default()
        cursor = Gdk.Cursor.new_for_display(display, type)
        self.window.get_window().set_cursor(cursor)

    def get_rotation(self, event):
        center = self.box_actor.get_center(self.handles) * array([self.aspect(), 1])
        click = array(self.relative_position(event)) * array([self.aspect(), 1])

        distance = click - center
        distance /= numpy.linalg.norm(distance)

        axis = array([1, 0])

        rot = math.atan2(distance[1], distance[0])\
              - math.atan2(axis[1], axis[0])

        return math.degrees(-rot)

    def on_motion(self, sink, event):

        if not self.selected:
            return

        #cursor change only when not dragging
        if not self.some_button_pressed:
            for actor in self.handles.values():
                if actor.is_clicked(self.relative_position(event)):

                    rot = self.get_rotation(event) % 360
                    if rot < 90:
                        self.set_cursor(Gdk.CursorType.BOTTOM_RIGHT_CORNER)
                    elif rot < 180:
                        self.set_cursor(Gdk.CursorType.BOTTOM_LEFT_CORNER)
                    elif rot < 270:
                        self.set_cursor(Gdk.CursorType.TOP_LEFT_CORNER)
                    else:
                        self.set_cursor(Gdk.CursorType.TOP_RIGHT_CORNER)

                    # dont check box if we have a hit
                    return

            if self.box_actor.is_clicked(self.relative_position(event), self.handles):
                self.set_cursor(Gdk.CursorType.PLUS) # inside box
            else:
                self.set_cursor(Gdk.CursorType.EXCHANGE) # rotate




        if self.focused_actor:
            #self.focused_actor.position = self.relative_position(event)

            scale_x = self.slider_box.sliders["scale-x"]
            scale_y = self.slider_box.sliders["scale-y"]

            center = self.box_actor.get_center(self.handles)

            distance = center - array(self.relative_position(event))

            length = numpy.sqrt(distance.dot(distance))

            scale_x.set(length / 1.4)
            scale_y.set(length / 1.4)

        elif self.dragged:
            pos = array(self.relative_position(event))

            self.set_cursor(Gdk.CursorType.FLEUR) # drag

            x = self.slider_box.sliders["translation-x"]
            y = self.slider_box.sliders["translation-y"]

            x.set((self.oldpos[0] + pos[0] * self.aspect()))
            y.set(self.oldpos[1] - pos[1])
        elif self.clicked_outside:
            rotation = self.slider_box.sliders["rotation-z"]
            rotation.set((self.oldrot + self.get_rotation(event)) % 360)

    def on_scroll(self, sink, event):
        print("deltas", event.get_scroll_deltas())
        print("direction", event.get_scroll_direction())

    def on_release(self, sink, event):
        self.focused_actor = None
        self.dragged = False
        self.clicked_outside = False
        self.some_button_pressed = False

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

    def is_clicked(self, click, handles):

        from shapely.geometry import Point
        from shapely.geometry.polygon import Polygon

        point = Point(*click)
        polygon = Polygon([handles["1BL"].position,
                           handles["2TL"].position,
                           handles["3TR"].position,
                           handles["4BR"].position])

        return polygon.contains(point)

    def get_center(self, handles):
        diagonal = array(handles["1BL"].position) - array(handles["3TR"].position)

        center = array(handles["3TR"].position) + diagonal / 2.0

        return center


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

        if self.selected:
            self.graphics["box"].draw(self.handles)
            self.graphics["handle"].draw_actors(self.handles.values())

        return True