__author__ = 'Lubosz Sarnecki'

from OpenGL.GL import *
from gi.repository import GstGL
import cairo


class Mesh():
    def __init__(self, type):
        self.type = type
        self.buffers = {}
        self.locations = {}
        self.element_sizes = {}

    def add(self, name, buffer, element_size):
        self.buffers[name] = buffer
        self.element_sizes[name] = element_size

    def set_index(self, index):
        self.index = index

    def bind(self, shader):
        for name in self.buffers:
            self.locations[name] = shader.shader.get_attribute_location(name)
            glVertexAttribPointer(
                self.locations[name],
                self.element_sizes[name],
                GL_FLOAT, GL_FALSE, 0,
                self.buffers[name])
            glEnableVertexAttribArray(self.locations[name])

    def draw(self):
        glDrawElements(self.type,
                       len(self.index),
                       GL_UNSIGNED_SHORT,
                       self.index)

    def unbind(self):
        for name in self.buffers:
            glDisableVertexAttribArray(self.locations[name])


class PlaneTriangleFan(Mesh):
    def __init__(self):
        Mesh.__init__(self, GL_TRIANGLE_STRIP)
        self.add(
            "position", [
                -1, 1, 0, 1,
                1, 1, 0, 1,
                1, -1, 0, 1,
                -1, -1, 0, 1], 4)
        self.add(
            "uv", [
                0.0, 0.0,
                1.0, 0.0,
                1.0, 1.0,
                0.0, 1.0], 2)
        self.set_index([0, 1, 3, 2])


class PlaneCairo(Mesh):
    def __init__(self, canvas_width, canvas_height, object_width, object_height):
        Mesh.__init__(self, GL_TRIANGLE_STRIP)

        w, h = object_width / canvas_width, \
               object_height / canvas_height

        self.add(
            "position", [
                -w, h, 0, 1,
                w, h, 0, 1,
                w, -h, 0, 1,
                -w, -h, 0, 1], 4)

        self.add(
            "uv", [
                0.0, 0.0,
                object_width, 0.0,
                object_width, object_height,
                0.0, object_height], 2)
        self.set_index([0, 1, 3, 2])


class Shader():
    def __init__(self, context, vert_name, frag_name):
        self.shader = GstGL.GLShader.new(context)

        vert = open("shaders/%s" % vert_name).read()
        frag = open("shaders/%s" % frag_name).read()

        self.shader.set_vertex_source(vert)
        self.shader.set_fragment_source(frag)

        if not self.shader.compile():
            exit()

    def use(self):
        return self.shader.use()

    def get_handle(self):
        return self.shader.get_program_handle()

    def set_matrix(self, name, matrix):
        location = glGetUniformLocation(self.get_handle(), name)
        glUniformMatrix4fv(location, 1, GL_FALSE, matrix)


class CairoTexture():
    def __init__(self, gl_id, width, height):
        self.width, self.height = width, height
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        self.ctx = cairo.Context(self.surface)
        glActiveTexture(gl_id)
        self.texture_handle = glGenTextures(1)

    def draw(self, callback):
        glBindTexture(GL_TEXTURE_RECTANGLE, self.texture_handle)
        callback(self.ctx, self.width, self.height)
        glTexImage2D(GL_TEXTURE_RECTANGLE,
                     0,
                     GL_RGBA,
                     self.width,
                     self.height,
                     0,
                     GL_BGRA,
                     GL_UNSIGNED_BYTE,
                     self.surface.get_data())
        glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_DECAL)

    def delete(self):
        if self.texture_handle:
            glDeleteTextures(self.texture_handle)