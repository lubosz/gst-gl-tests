__author__ = 'Lubosz Sarnecki'

from OpenGL.GL import *


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
            self.locations[name] = shader.get_attribute_location(name)
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