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
        self.window = None

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

    def on_scroll(self, sink, event):
        print("deltas", event.get_scroll_deltas())
        print("direction", event.get_scroll_direction())

    def reshape(self, sink, context, width, height):
        self.width, self.height = width, height
        if not self.init:
            self.init_gl(context)
            self.init = True
        glViewport(0, 0, width, height)
        return True

    def init_gl(self, context):
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_TEXTURE_RECTANGLE)


class Actor():
    def __init__(self, drag, x=0, y=0):
        self.position = (x, y)
        self.clicked = False
        self.initital_position = self.position
        self.drag = drag

    def is_clicked(self, click):
        vclick = Graphene.Vec2.alloc()
        vclick.init(click[0], click[1])
        vpos = Graphene.Vec2.alloc()
        vpos.init(self.position[0], self.position[1])
        vdistance = vclick.subtract(vpos)

        return vdistance.length() < 0.1

    def reposition(self, matrix, aspect):
            vector = numpy.array([self.initital_position[0] * math.pi,
                                  -self.initital_position[1],
                                  0, 1])
            vector_transformed = numpy.dot(vector, matrix)

            self.position = (vector_transformed[0] / aspect,
                               -vector_transformed[1])

    def model_matrix(self):
        model_matrix = Graphene.Matrix.alloc()

        translation_vector = Graphene.Point3D.alloc()
        translation_vector.init(self.position[0], self.position[1], 0)

        model_matrix.init_translate(translation_vector)

        return matrix_to_array(model_matrix)


class BoxActor(Actor):
    def __init__(self, drag):
        Actor.__init__(self, drag)

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

        self.corner_handles = {
            "1BL": Actor(self.scale_keep_aspect, -1, -1),
            "2TL": Actor(self.scale_keep_aspect, -1, 1),
            "3TR": Actor(self.scale_keep_aspect, 1, 1),
            "4BR": Actor(self.scale_keep_aspect, 1, -1)}

        self.edge_handles = {
            "left": Actor(self.scale_height, -1, 0),
            "right": Actor(self.scale_height, 1, 0),
            "top": Actor(self.scale_width, 0, 1),
            "bottom": Actor(self.scale_width, 0, -1)}

        self.graphics["handle"] = HandleGraphic(100, 100)
        self.graphics["video"] = VideoGraphic()
        self.graphics["box"] = BoxGraphic(1280, 720, self.corner_handles.values())

        self.handles = []

        for handle in self.corner_handles.values():
            self.handles.append(handle)
        for handle in self.edge_handles.values():
            self.handles.append(handle)

        self.box_actor = BoxActor(self.translate)
        self.selected = False
        self.slider_box = None
        self.action = None

    def deselect(self):
        self.selected = False
        # default
        self.set_cursor(Gdk.CursorType.ARROW)

    def init_gl(self, context):
        Scene.init_gl(self, context)

        self.graphics["handle"].init_gl(context, self.width, self.height)
        self.graphics["box"].init_gl(context, self.width, self.height)
        self.graphics["video"].init_gl(context)

        self.init = True

    def reposition(self, matrix):
        for handle in self.handles:
            handle.reposition(matrix, self.aspect())

    def draw(self, sink, context, video_texture, w, h):
        if not self.init:
            return

        context.clear_shader()

        glClearColor(0, 0, 0, 1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        self.graphics["video"].draw(video_texture, numpy.identity(4))
        context.clear_shader()

        if self.selected:
            self.graphics["box"].draw(self.corner_handles)
            self.graphics["handle"].draw_actors(self.handles)

        return True

    def get_rotation(self, event):
        center = self.box_actor.get_center(self.corner_handles) * array([self.aspect(), 1])
        click = array(self.relative_position(event)) * array([self.aspect(), 1])

        distance = click - center
        distance /= numpy.linalg.norm(distance)

        axis = array([1, 0])

        rot = math.atan2(distance[1], distance[0]) \
              - math.atan2(axis[1], axis[0])

        return math.degrees(-rot)

    def scale_width(self, event):
        scale_y = self.slider_box.sliders["scale-y"]
        center = self.box_actor.get_center(self.corner_handles)
        distance = center - array(self.relative_position(event))
        length = numpy.sqrt(distance.dot(distance))
        scale_y.set(length)

    def scale_height(self, event):
        scale_x = self.slider_box.sliders["scale-x"]
        center = self.box_actor.get_center(self.corner_handles)
        distance = center - array(self.relative_position(event))
        length = numpy.sqrt(distance.dot(distance))
        scale_x.set(length)

    def scale_keep_aspect(self, event):
        old_aspect = self.old_scale[0] / self.old_scale[1]
        scale_x = self.slider_box.sliders["scale-x"]
        scale_y = self.slider_box.sliders["scale-y"]
        center = self.box_actor.get_center(self.corner_handles)
        distance = center - array(self.relative_position(event))
        length = numpy.sqrt(distance.dot(distance))
        scale_x.set(old_aspect * length / math.sqrt(2))
        scale_y.set(length / math.sqrt(2))

    def rotate(self, event):
        rotation = self.slider_box.sliders["rotation-z"]
        rotation.set((self.oldrot + self.get_rotation(event)) % 360)

    def translate(self, event):
        pos = array(self.relative_position(event))

        # drag cursor
        self.set_cursor(Gdk.CursorType.FLEUR)

        x = self.slider_box.sliders["translation-x"]
        y = self.slider_box.sliders["translation-y"]

        x.set((self.oldpos[0] + pos[0] * self.aspect()))
        y.set(self.oldpos[1] - pos[1])

    def on_press(self, event):
        # Right click
        if event.get_button()[1] == 3:
            self.deselect()
        # Left click
        elif event.get_button()[1] == 1:
            for actor in self.handles:
                if actor.is_clicked(self.relative_position(event)):
                    self.action = actor.drag
                    self.old_scale = (self.slider_box.sliders["scale-x"].get(),
                                      self.slider_box.sliders["scale-y"].get())
                    actor.clicked = True
                    return

            if self.box_actor.is_clicked(self.relative_position(event), self.corner_handles):
                self.action = self.translate
                self.selected = True

                pos = self.relative_position(event)

                self.oldpos = ((self.slider_box.sliders["translation-x"].get() - pos[0] * self.aspect()),
                               self.slider_box.sliders["translation-y"].get() + pos[1])
            else:
                #clicked outside of box
                self.action = self.rotate

                self.oldrot = self.slider_box.sliders["rotation-z"].get() - self.get_rotation(event)

    def on_motion(self, sink, event):
        if not self.selected:
            return

        self.action(event)

    def on_release(self, sink, event):
        self.focused_actor = None
        self.action = self.on_hover

        for actor in self.handles:
            actor.clicked = False

    # cursor stuff
    def on_hover(self, event):
        for actor in self.corner_handles.values():
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

        for actor in self.edge_handles.values():
            if actor.is_clicked(self.relative_position(event)):

                rot = (self.get_rotation(event) - 45) % 360
                if rot < 90:
                    self.set_cursor(Gdk.CursorType.BOTTOM_SIDE)
                elif rot < 180:
                    self.set_cursor(Gdk.CursorType.LEFT_SIDE)
                elif rot < 270:
                    self.set_cursor(Gdk.CursorType.TOP_SIDE)
                else:
                    self.set_cursor(Gdk.CursorType.RIGHT_SIDE)

                # dont check box if we have a hit
                return

        if self.box_actor.is_clicked(self.relative_position(event), self.corner_handles):
            # inside box
            self.set_cursor(Gdk.CursorType.PLUS)
        else:
            # rotate
            self.set_cursor(Gdk.CursorType.EXCHANGE)