#!/usr/bin/env python3

import numpy
from cairo import *
from sdl2 import *
from OpenGL.GL import *

from math import pi

def init_gl():
    print("OpenGL version:", glGetString(GL_VERSION))
    print("OpenGL vendor:", glGetString(GL_VENDOR))
    print("OpenGL renderer:", glGetString(GL_RENDERER))

    glClearColor(0.0, 0.0, 0.0, 0.0)
    glDisable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_TEXTURE_RECTANGLE)


def draw(width, height, surface, texture_id):
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glClear(GL_COLOR_BUFFER_BIT)

    glPushMatrix()

    glBindTexture(GL_TEXTURE_RECTANGLE, texture_id)
    glTexImage2D(GL_TEXTURE_RECTANGLE,
                 0,
                 GL_RGBA,
                 width,
                 height,
                 0,
                 GL_BGRA,
                 GL_UNSIGNED_BYTE,
                 surface.get_data())

    glColor3f(0.25, 0.5, 1.0)
    glBegin(GL_QUADS)
    glTexCoord2f(0.0, 0.0)
    glVertex2f(0.0, 0.0)
    glTexCoord2f(width, 0.0)
    glVertex2f(1.0, 0.0)
    glTexCoord2f(width, height)
    glVertex2f(1.0, 1.0)
    glTexCoord2f(0.0, height)
    glVertex2f(0.0, 1.0)
    glEnd()

    glPopMatrix()


def resize(width, height):
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0.0, 1.0, 0.0, 1.0, -1.0, 1.0)

    glClear(GL_COLOR_BUFFER_BIT)

    #glDeleteTextures(texture_id)
    texture_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_RECTANGLE, texture_id)
    glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_DECAL)

    return texture_id


def render_cairo(cr, width, height):
    cr.save()

    # clear background
    cr.set_operator(OPERATOR_OVER)
    cr.scale(width, height)
    cr.set_source_rgba(0.0, 0.0, 0.25, 1.0)
    cr.paint()


    pat = LinearGradient(0.0, 0.0, 0.0, 1.0)
    # First stop, 50% opacity
    pat.add_color_stop_rgba(1, 0.7, 0, 0, 0.5)
    # Last stop, 100% opacity
    pat.add_color_stop_rgba(0, 0.9, 0.7, 0.2, 1)

    # Rectangle(x0, y0, x1, y1)
    cr.rectangle(0, 0, 1, 1)
    cr.set_source(pat)
    cr.fill()

    # Changing the current transformation matrix
    cr.translate(0.1, 0.1)

    cr.move_to(0, 0)
    # Arc(cx, cy, radius, start_angle, stop_angle)
    cr.arc(0.2, 0.1, 0.1, -pi/2, 0)
    # Line to (x,y)
    cr.line_to(0.5, 0.1)
    # Curve(x1, y1, x2, y2, x3, y3)
    cr.curve_to (0.5, 0.2, 0.5, 0.4, 0.2, 0.8)
    cr.close_path()

    # Solid color
    cr.set_source_rgb(0.3, 0.2, 0.5)
    cr.set_line_width(0.02)
    cr.stroke()

    #cr.rectangle(0.0, 0.0, 1, 1)
    #cr.set_source(linear)
    #cr.fill()

    cr.restore()


def main():

    width, height = 256, 256

    SDL_Init(SDL_INIT_VIDEO)

    window = SDL_CreateWindow(b"OpenGL demo",
                              SDL_WINDOWPOS_UNDEFINED,
                              SDL_WINDOWPOS_UNDEFINED,
                              width, height,
                              SDL_WINDOW_OPENGL)

    context = SDL_GL_CreateContext(window)

    SDL_GL_SetSwapInterval(1)

    # create cairo-surface/context to act as OpenGL-texture source
    surface = ImageSurface(FORMAT_ARGB32, width, height)
    #buffer = numpy.zeros(height*width*4, dtype=numpy.uint8)
    #surface = ImageSurface.create_for_data(buffer, FORMAT_ARGB32, width, height)
    cr = Context(surface)

    init_gl()
    texture_id = resize(width, height)

    event = SDL_Event()
    running = True
    while running:
        while SDL_PollEvent(ctypes.byref(event)) != 0:
            if event.type == SDL_QUIT:
                running = False
            if event.key.keysym.sym == SDLK_ESCAPE:
                running = False

            """
            if event.type == SDL_VIDEORESIZE:
                width = event.resize.w
                height = event.resize.h
                SDL_SetVideoMode(width, height, 0, SDL_OPENGL | SDL_RESIZABLE)
                resize(width, height, texture_id)
                cr.destroy()
                cr = create_cairo_context(width, height, 4, surf, surf_data)
            """

        render_cairo(cr, width, height)
        draw(width, height, surface, texture_id)
        SDL_GL_SwapWindow(window)

    # clear resources before exit
    glDeleteTextures(texture_id)

    SDL_GL_DeleteContext(context)
    SDL_DestroyWindow(window)
    SDL_Quit()

    return 0

main()