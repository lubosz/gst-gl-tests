from gi.repository import Clutter
import cairo

from math import pi, sin, cos, ceil

MINIMAL_POINT_SIZE = 7
DEFAULT_POINT_SIZE = 25

def hex_to_rgb(value):
    return tuple(float(int(value[i:i + 2], 16)) / 255.0 for i in range(0, 6, 2))

class Point():
    """
    Draw a point, used as a handle for the transformation box
    """

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.color = hex_to_rgb('49a0e0')
        self.clickedColor = hex_to_rgb('ffa854')
        #self.set_width(settings.pointSize)
        #self.color = Clutter.Color.new(255, 0, 0, 196)
        #self.clicked_color = Clutter.Color.new(0, 255, 0, 196)
        self.set_width(DEFAULT_POINT_SIZE)
        self.clicked = False

    def set_position(self, x, y):
        self.x = x
        self.y = y

    def set_width(self, width):
        self.width = width
        self.radius = width / 2

    def is_clicked(self, event):
        is_right_of_left = event.x > self.x - self.radius
        is_left_of_right = event.x < self.x + self.radius
        is_below_top = event.y > self.y - self.radius
        is_above_bottom = event.y < self.y + self.radius

        if is_right_of_left and is_left_of_right and is_below_top and is_above_bottom:
            self.clicked = True
            return True

    def draw(self, cr):
        linear = cairo.LinearGradient(self.x, self.y - self.radius,
                                    self.x, self.y + self.radius)
        linear.add_color_stop_rgba(0.00, .6, .6, .6, 1)
        linear.add_color_stop_rgba(0.50, .4, .4, .4, .1)
        linear.add_color_stop_rgba(0.60, .4, .4, .4, .1)
        linear.add_color_stop_rgba(1.00, .6, .6, .6, 1)

        radial = cairo.RadialGradient(self.x + self.radius / 2,
                                    self.y - self.radius / 2, 1,
                                    self.x, self.y,
                                    self.radius)
        if self.clicked:
            radial.add_color_stop_rgb(0, *self.clickedColor)
        else:
            radial.add_color_stop_rgb(0, *self.color)
        radial.add_color_stop_rgb(1, 0.1, 0.1, 0.1)
        radial_glow = cairo.RadialGradient(self.x, self.y,
                                        self.radius * .9,
                                        self.x, self.y,
                                        self.radius * 1.2)
        radial_glow.add_color_stop_rgba(0, 0.9, 0.9, 0.9, 1)
        radial_glow.add_color_stop_rgba(1, 0.9, 0.9, 0.9, 0)

        cr.set_source(radial_glow)
        cr.arc(self.x, self.y, self.radius * 1.2, 0, 2 * pi)
        cr.fill()
        cr.arc(self.x, self.y, self.radius * .9, 0, 2 * pi)
        cr.set_source(radial)
        cr.fill()
        cr.arc(self.x, self.y, self.radius * .9, 0, 2 * pi)
        cr.set_source(linear)
        cr.fill()

(NO_ACTOR,
 RECTANGLE,
 TOP_LEFT,
 BOTTOM_LEFT,
 TOP_RIGHT,
 BOTTOM_RIGHT,
 LEFT,
 RIGHT,
 TOP,
 BOTTOM) = list(range(10))


class Area():
  def __init__(self, x, y, width, height):
    self.width = width
    self.height = height
    self.x = x
    self.y = y

class TransformationBox(Clutter.Actor):
    """
    Box for transforming the video on the ViewerWidget
    """
    
    click_x = 0
    click_y = 0

    def __init__(self, canvas, x, y, w, h):
        Clutter.Actor.__init__(self)
        self.set_content (canvas)
        self.clicked_actor = NO_ACTOR
        self.left_factor = 0
        self.right_factor = 1
        self.top_factor = 0
        self.bottom_factor = 1
        self.center_factor = Point(0.5, 0.5)
        self.transformation_properties = None
        self.points = {}
        
        self.area = Area(x, y, w, h)
        self.left = x
        self.right = x + w
        self.top = y
        self.bottom = y + h
        self.center = Point((self.left + self.right) / 2, (self.top + self.bottom) / 2)
        self.init_points()
        self.update_width()
        
        canvas.connect ("draw", self.draw)

    def is_clicked(self, event):
        is_right_of_left = event.x > self.left
        is_left_of_right = event.x < self.right
        is_below_top = event.y > self.top
        is_above_bottom = event.y < self.bottom

        if is_right_of_left and is_left_of_right and is_below_top and is_above_bottom:
            return True

    def point_setup(self):
        return {
          #corner points
          TOP_LEFT : (self.left, self.top),
          TOP_RIGHT : (self.right, self.top),
          BOTTOM_LEFT : (self.left, self.bottom),
          BOTTOM_RIGHT : (self.right, self.bottom),
          #edge points
          TOP : (self.center.x, self.top),
          BOTTOM : (self.center.x, self.bottom),
          LEFT : (self.left, self.center.y),
          RIGHT : (self.right, self.center.y)
        }

    def init_points(self):
        for enum, location in self.point_setup().items():
          self.points[enum] = Point(*location)
          #print(enum, location)
  
    def update_points(self):
        self.update_width()
         
        for enum, location in self.point_setup().items():
          self.points[enum].set_position(*location)
          print("Update", enum, location)

        # shrink points for smaller areas
        if self.width < 100 or self.height < 100:
            if self.width < self.height:
                point_width = self.width / 4.0
            else:
                point_width = self.height / 4.0

            # minimal point size
            if point_width < MINIMAL_POINT_SIZE:
                point_width = MINIMAL_POINT_SIZE
        else:
            point_width = DEFAULT_POINT_SIZE

        for point in self.points.values():
            point.set_width(point_width)

    def update_scale(self):
        self.scale_x = (self.right_factor - self.left_factor) / 2.0
        self.scale_y = (self.bottom_factor - self.top_factor) / 2.0

    def update_center(self):
        self.center_factor.x = (self.left_factor + self.right_factor) / 2.0
        self.center_factor.y = (self.top_factor + self.bottom_factor) / 2.0

        self.center.x = self.area.width * self.center_factor.x
        self.center.y = self.area.height * self.center_factor.y

    def update_width(self):
        self.width = self.right - self.left
        self.height = self.bottom - self.top

    def update_factors(self):
        self.bottom_factor = float(self.bottom) / float(self.area.height)
        self.top_factor = float(self.top) / float(self.area.height)
        self.left_factor = float(self.left) / float(self.area.width)
        self.right_factor = float(self.right) / float(self.area.width)

    def update_size(self, area):
        if area.width == 0 or area.height == 0:
            return
        self.area = area
        self.update_absolute()

    def update_absolute(self):
        self.top = self.top_factor * self.area.height
        self.left = self.left_factor * self.area.width
        self.bottom = self.bottom_factor * self.area.height
        self.right = self.right_factor * self.area.width
        self.update_center()

    def draw (self, canvas, cr, width, height):
      self.update_points()
    
      cr.save ()
      # clear the contents of the canvas, to avoid painting
      # over the previous frame
      cr.set_operator (cairo.OPERATOR_CLEAR)
      cr.paint ()
      cr.restore ()
      cr.set_operator (cairo.OPERATOR_OVER)
    
      # main box
      cr.set_source_rgba(0.5, 0.5, 0.5, 0.7)
      cr.rectangle(self.left, self.top, self.right - self.left, self.bottom - self.top)
      cr.stroke()

      for point in list(self.points.values()):
          point.draw(cr)
      return True

    def button_press(self, event):
        # translate when zoomed out
        #event.x -= self.area.x
        #event.y -= self.area.y
        for type, point in list(self.points.items()):
            if point.is_clicked(event):
                self.clicked_actor = type
                return

        if self.is_clicked(event):
            self.clicked_actor = RECTANGLE
            self.click_x = event.x
            self.click_y = event.y
        else:
            self.clicked_actor = NO_ACTOR

    def check_negative_scale(self):
        if self.right < self.left:
            if self.clicked_actor in [RIGHT, BOTTOM_RIGHT, TOP_RIGHT]:
                self.right = self.left
            else:
                self.left = self.right
        if self.bottom < self.top:
            if self.clicked_actor == [BOTTOM, BOTTOM_RIGHT, BOTTOM_LEFT]:
                self.bottom = self.top
            else:
                self.top = self.bottom

    def translate(self, event):
        rel_x = self.click_x - event.x
        rel_y = self.click_y - event.y

        self.center.x -= rel_x
        self.center.y -= rel_y

        self.left -= rel_x
        self.right -= rel_x
        self.top -= rel_y
        self.bottom -= rel_y

        self.click_x = event.x
        self.click_y = event.y

    def motion(self, event):
        # translate when zoomed out
        #event.x -= self.area.x
        #event.y -= self.area.y
        aspect = float(self.area.width) / float(self.area.height)
        self.update_width()

        if self.clicked_actor == NO_ACTOR:
            return False
        elif self.clicked_actor == RECTANGLE:
            self.translate(event)
        elif self.clicked_actor == TOP_LEFT:
            self.left = event.x
            self.top = self.bottom - self.width / aspect
        elif self.clicked_actor == BOTTOM_LEFT:
            self.left = event.x
            self.bottom = self.top + self.width / aspect
        elif self.clicked_actor == TOP_RIGHT:
            self.right = event.x
            self.top = self.bottom - self.width / aspect
        elif self.clicked_actor == BOTTOM_RIGHT:
            self.right = event.x
            self.bottom = self.top + self.width / aspect
        elif self.clicked_actor == LEFT:
            self.left = event.x
        elif self.clicked_actor == RIGHT:
            self.right = event.x
        elif self.clicked_actor == TOP:
            self.top = event.y
        elif self.clicked_actor == BOTTOM:
            self.bottom = event.y
        self.check_negative_scale()
        self.update_factors()
        self.update_center()
        self.update_scale()
        return True

    def button_release(self):
        for point in list(self.points.values()):
            point.clicked = False
        self.clicked_actor = NO_ACTOR

    """
    def set_transformation_properties(self, transformation_properties):
        self.transformation_properties = transformation_properties
        self.update_from_effect(transformation_properties.effect)

    def update_from_effect(self, effect):
        self.scale_x = effect.get_property("scale-x")
        self.scale_y = effect.get_property("scale-y")
        self.center_factor.x = 2 * (effect.get_property("tilt-x") - 0.5) + self.scale_x
        self.center_factor.y = 2 * (effect.get_property("tilt-y") - 0.5) + self.scale_y
        self.left_factor = self.center_factor.x - self.scale_x
        self.right_factor = self.center_factor.x + self.scale_x
        self.top_factor = self.center_factor.y - self.scale_y
        self.bottom_factor = self.center_factor.y + self.scale_y
        self.update_absolute()
        self.update_factors()
        self.update_center()
        self.update_scale()
        self.update_points()

    def update_effect_properties(self):
        if self.transformation_properties:
            self.transformation_properties.disconnectSpinButtonsFromFlush()
            values = self.transformation_properties.spin_buttons
            values["tilt_x"].set_value((self.center_factor.x - self.scale_x) / 2.0 + 0.5)
            values["tilt_y"].set_value((self.center_factor.y - self.scale_y) / 2.0 + 0.5)

            values["scale_x"].set_value(self.scale_x)
            values["scale_y"].set_value(self.scale_y)
            self.transformation_properties.connectSpinButtonsToFlush()
    """
