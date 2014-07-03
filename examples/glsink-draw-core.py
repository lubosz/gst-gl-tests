#!/usr/bin/env python3

from gi.repository import Gdk, Gst, Gtk, GdkX11, GstVideo, GstGL, Graphene

from OpenGL.GL import *

import numpy
import signal

signal.signal(signal.SIGINT, signal.SIG_DFL)

from IPython import embed


def matrix_to_array(m):
    result = []
    for x in range(0, 4):
        result.append([m.get_value(x, 0),
                       m.get_value(x, 1),
                       m.get_value(x, 2),
                       m.get_value(x, 3)])
    return numpy.array(result, 'd')


class ShaderGLSink():
    vertex_src = """
      attribute vec4 position;
      attribute vec2 uv;
      uniform mat4 mvp;
      varying vec2 out_uv;
      void main()
      {
         gl_Position = mvp * position;
         out_uv = uv;
      }
    """

    fragment_src = """
      varying vec2 out_uv;
      uniform sampler2D texture;
      void main()
      {
        gl_FragColor = texture2D (texture, out_uv);
      }
    """

    vertex2_src = """
      attribute vec4 position;
      attribute vec2 uv;
      uniform mat4 mvp;
      varying vec2 out_uv;
      void main()
      {
         gl_Position = mvp * position;
         out_uv = uv;
      }
    """

    fragment2_src = """
      varying vec2 out_uv;
      uniform sampler2D texture;
      void main()
      {
        gl_FragColor = vec4(vec3(1) - texture2D (texture, out_uv).xyz, 1);
      }
    """

    def reshape(self, sink, context, width, height):
        #context.gen_shader(vertex_src, fragment_src, shader)
        self.shader = GstGL.GLShader.new(context)
        self.shader.set_fragment_source(self.fragment_src)
        self.shader.set_vertex_source(self.vertex_src)
        if not self.shader.compile():
            exit()


        self.shader2 = GstGL.GLShader.new(context)
        self.shader2.set_fragment_source(self.fragment2_src)
        self.shader2.set_vertex_source(self.vertex2_src)
        if not self.shader2.compile():
            exit()

        glViewport(0, 0, width, height)

        self.mvp = self.build_mvp()
        self.aspect = width/height

        return True

    def build_model(self):
        model_matrix = Graphene.Matrix.alloc()
        model_matrix.init_rotate(self.xrotation, Graphene.vec3_x_axis())
        model_matrix.rotate(self.yrotation, Graphene.vec3_y_axis())
        model_matrix.rotate(self.zrotation, Graphene.vec3_z_axis())
        model_matrix.scale(self.xscale, self.yscale, 1.0)

        translation_vector = Graphene.Point3D.alloc()
        translation_vector.init(self.xtranslation, self.ytranslation, self.ztranslation)
        model_matrix.translate(translation_vector)

        return matrix_to_array(model_matrix)

    def build_projection(self):
        projection_matrix = Graphene.Matrix.alloc()
        if self.ortho:
            projection_matrix.init_ortho(-self.aspect, self.aspect, -1, 1, self.znear, self.zfar)
        else:
            projection_matrix.init_perspective(self.fovy, self.aspect, self.znear, self.zfar)
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

    def draw_box(self, context, texture, mvp):
        positions = numpy.array([-self.aspect, 1.0, 0.0, 1.0,
                                 self.aspect, 1.0, 0.0, 1.0,
                                 self.aspect, -1.0, 0.0, 1.0,
                                 -self.aspect, -1.0, 0.0, 1.0])

        uvs = numpy.array([0.0, 0.0,
                           1.0, 0.0,
                           1.0, 1.0,
                           0.0, 1.0])

        indices = [0, 1, 2, 3, 0]

        context.clear_shader()
        glBindTexture(GL_TEXTURE_2D, 0)

        #glClearColor(0, 0, 0, 1)
        #glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        self.shader2.use()

        position_loc = self.shader2.get_attribute_location("position")

        uv_loc = self.shader2.get_attribute_location("uv")

        # Load the vertex position
        glVertexAttribPointer(position_loc, 4, GL_FLOAT, GL_FALSE, 0, positions)

        # Load the texture coordinate
        glVertexAttribPointer(uv_loc, 2, GL_FLOAT, GL_FALSE, 0, uvs)

        glEnableVertexAttribArray(position_loc)
        glEnableVertexAttribArray(uv_loc)

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, texture)
        #self.shader.set_uniform_1i("texture", 0)

        location = glGetUniformLocation(self.shader2.get_program_handle(), "mvp")

        glUniformMatrix4fv(location, 1, GL_FALSE, mvp)

        glDrawElements(GL_QUADS, 5, GL_UNSIGNED_SHORT, indices)

        glDisableVertexAttribArray(position_loc)
        glDisableVertexAttribArray(uv_loc)

        context.clear_shader()

    def draw_background(self, context, texture, mvp):
        positions = numpy.array([-self.aspect, 1.0, 0.0, 1.0,
                                 self.aspect, 1.0, 0.0, 1.0,
                                 self.aspect, -1.0, 0.0, 1.0,
                                 -self.aspect, -1.0, 0.0, 1.0])

        uvs = numpy.array([0.0, 0.0,
                           1.0, 0.0,
                           1.0, 1.0,
                           0.0, 1.0])

        indices = [0, 1, 2, 3, 0]

        context.clear_shader()
        glBindTexture(GL_TEXTURE_2D, 0)

        glClearColor(0, 0, 0, 1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        self.shader.use()

        position_loc = self.shader.get_attribute_location("position")

        uv_loc = self.shader.get_attribute_location("uv")

        # Load the vertex position
        glVertexAttribPointer(position_loc, 4, GL_FLOAT, GL_FALSE, 0, positions)

        # Load the texture coordinate
        glVertexAttribPointer(uv_loc, 2, GL_FLOAT, GL_FALSE, 0, uvs)

        glEnableVertexAttribArray(position_loc)
        glEnableVertexAttribArray(uv_loc)

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, texture)
        #self.shader.set_uniform_1i("texture", 0)

        location = glGetUniformLocation(self.shader.get_program_handle(), "mvp")

        glUniformMatrix4fv(location, 1, GL_FALSE, mvp)

        glDrawElements(GL_TRIANGLE_STRIP, 5, GL_UNSIGNED_SHORT, indices)

        glDisableVertexAttribArray(position_loc)
        glDisableVertexAttribArray(uv_loc)

        context.clear_shader()

    def draw(self, sink, context, texture, width, height):

        self.zrotation += 2.0
        #self.yrotation += 1.0
        self.xtranslation = 0.0
        self.mvp = self.build_mvp()

        if not self.shader:
            return

        self.draw_background(context, texture, self.mvp)

        #self.xtranslation = 1.0
        #self.mvp = self.build_mvp()

        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        #glBindTexture(GL_TEXTURE_2D, 0)

        glLineWidth(40)

        self.draw_box(context, texture, self.mvp)

        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)



        return True

    @staticmethod
    def window_closed(widget, event, pipeline):
        widget.hide()
        pipeline.set_state(Gst.State.NULL)
        Gtk.main_quit()

    def __init__(self):
        Gdk.init([])
        Gtk.init([])
        Gst.init([])

        pipeline = Gst.Pipeline()
        src = Gst.ElementFactory.make("videotestsrc", None)
        trans = Gst.ElementFactory.make("gltransformation", None)
        sink = Gst.ElementFactory.make("glimagesink", None)

        if not sink or not src:
            print("GL elements not available.")
            exit()

        self.shader = None
        self.mvp = None

        self.xtranslation = 0
        self.ytranslation = 0
        self.ztranslation = 0

        self.ortho = False

        self.xrotation = 0
        self.yrotation = 0
        self.zrotation = 0
        self.xscale = 0.5
        self.yscale = 0.5

        self.fovy = 90.0

        self.aspect = 320.0/240.0
        self.znear = 0.1
        self.zfar = 100.0

        pipeline.add(src, trans, sink)

        src.link(trans)
        trans.link(sink)
        window = Gtk.Window()
        window.connect("delete-event", self.window_closed, pipeline)
        window.set_default_size(320, 240)
        window.set_title("Hello OpenGL Sink!")

        sink.connect("client-draw", self.draw)
        sink.connect("client-reshape", self.reshape)

        #trans.set_property("rotation-z", 45.0)
        drawing_area = Gtk.DrawingArea()
        drawing_area.set_double_buffered(True)
        window.add(drawing_area)

        window.show_all()

        xid = drawing_area.get_window().get_xid()
        sink.set_window_handle(xid)

        if pipeline.set_state(Gst.State.PLAYING) == Gst.StateChangeReturn.FAILURE:
            pipeline.set_state(Gst.State.NULL)
        else:
            Gtk.main()


ShaderGLSink()
