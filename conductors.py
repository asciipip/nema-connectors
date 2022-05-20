#!/usr/bin/env python3
"""Provides classes for the basic shapes used by plug conductors."""

import cmath
import math

class DConductor:
    """A conductor whose outline forms a "D" shape.

    The curve of the "D" is done at the positive end of the longest
    dimension.  If the dimensions are equal, it is done at the positive
    end of the x dimension.  It may be repositioned by giving a `rotation`
    in degrees.
    """
    def __init__(self, width, height, x=0, y=0, rotation=0):
        self.width = width
        self.height = height
        self.x = x
        self.y = y
        self.rotation = rotation

    def draw(self, drawing, color='black'):
        path = drawing.path(fill=color)
        if color == 'white':
            path['stroke'] = 'black'
            path['stroke-width'] = OUTLINE_WIDTH
            
        if self.rotation == 0:
            x_offset = self.x
            y_offset = self.y
        else:
            x_offset = 0
            y_offset = 0
            if self.y == 0:
                path['transform'] = 'translate({}) rotate({})'.format(self.x, self.rotation)
            else:
                path['transform'] = 'translate({} {}) rotate({})'.format(
                    self.x, self.y, self.rotation)

        path.push('M', (x_offset - self.width/2, y_offset - self.height/2))
        if self.width >= self.height:
            side_length = self.width - self.height/2
            path.push('h', side_length)
            path.push_arc((0, self.height), 0, self.height/2, angle_dir='+')
            path.push('h', -side_length)
        else:
            side_length = self.height - self.width/2
            path.push('v', side_length)
            path.push_arc((self.width, 0), 0, self.width/2, angle_dir='-')
            path.push('v', -side_length)
        path.push('Z')
        return path

class IConductor:
    """A conductor that forms a straight line (or "I" shape)."""
    def __init__(self, width, height, x=0, y=0):
        self.width = width
        self.height = height
        self.x = x
        self.y = y

    def draw(self, drawing, color='black'):
        path = drawing.rect((self.x - self.width/2, self.y - self.height/2),
                            (self.width, self.height),
                            fill=color)
        if color == 'white':
            path['stroke'] = 'black'
            path['stroke-width'] = OUTLINE_WIDTH
            
        return path

class LConductor:
    """A conductor that forms roughly an "L" shape.

    `start` and `end` must be (x, y) tuples.  `sweep_dir` is either '+' or
    '-', mirroring the sweep flag on the SVG Path elliptical arc commands.
    """
    def __init__(self, width, start, end, sweep_dir):
        if sweep_dir not in ['+', '-']:
            raise ValueError('Invalid sweep_dir: {}'.format(sweep_dir))
        self.width = width
        self.start = start
        self.end = end
        self.sweep_dir = sweep_dir
        self.x_sign = math.copysign(1, self.end[0] - self.start[0])
        self.y_sign = math.copysign(1, self.end[1] - self.start[1])
        if self.x_sign == self.y_sign:
            self.x_first = sweep_dir == '+'
        else:
            self.x_first = sweep_dir == '-'

    def draw(self, drawing, color='black'):
        assert color != 'white', 'White L conductors not yet implemented.'
        path = drawing.path(fill='none', stroke=color, stroke_width=self.width)
        path.push('M', self.start)
        if self.x_first:
            path.push('h', self.end[0] - self.start[0] - self.x_sign * self.width/2)
        else:
            path.push('v', self.end[1] - self.start[1] - self.y_sign * self.width/2)
        path.push_arc(
            (self.width/2 * self.x_sign, self.width/2 * self.y_sign), 0,
            self.width/2, large_arc=False, absolute=False,
            angle_dir=self.sweep_dir)
        if self.x_first:
            path.push('V', self.end[1])
        else:
            path.push('H', self.end[0])

        return path

class OConductor:
    """A conductor whose shape is a circle."""
    def __init__(self, diameter, x=0, y=0):
        self.radius = diameter / 2
        self.x = x
        self.y = y

    def draw(self, drawing, color='black'):
        path = drawing.circle((self.x, self.y), self.radius, fill=color)
        if color == 'white':
            path['stroke'] = 'black'
            path['stroke-width'] = OUTLINE_WIDTH
        return path

class TConductor:
    """A conductor whose shape is an upper-case "T".

    `x` and `y` give the center of the intersection of the lines.
    `vertical_length` is measured from the top of the crossbar to the far
    end of the vertical bar.  The vertical bar extends downwards (negative
    y direction) from the intersection.  `rotation` (in degrees) may be
    used to reorient the T.
    """
    def __init__(self, width, crossbar_length, vertical_length, x=0, y=0, rotation=0):
        self.width = width
        self.crossbar_length = crossbar_length
        self.vertical_length = vertical_length
        self.x = x
        self.y = y
        self.rotation = rotation

    def draw(self, drawing, color='black'):
        assert color != 'white', 'White T conductors not yet implemented.'
        path = drawing.path(fill='none', stroke=color, stroke_width=self.width)
        if self.rotation != 0:
            path['transform'] = 'rotate({} {},{})'.format(self.rotation, self.x, self.y)
        path.push('M', (self.x - self.crossbar_length/2, self.y))
        path.push('h', self.crossbar_length)
        path.push('m', (-self.crossbar_length/2, 0))
        path.push('v', -(self.vertical_length - self.width/2))
        return path

class ArcConductor:
    """A conductor that follows an arc segment on a circle centered on the
    connector.

    Angle measurements are in degrees measured from the positive x axis.
    """
    def __init__(self, width, radius, start_angle, end_angle):
        self.width = width
        self.radius = radius
        start_rad = start_angle / 180 * math.pi
        end_rad = end_angle / 180 * math.pi
        start_complex = cmath.rect(radius, start_rad)
        end_complex = cmath.rect(radius, end_rad)
        self.start = (start_complex.real, start_complex.imag)
        self.end = (end_complex.real, end_complex.imag)
        if start_angle < end_angle:
            self.angle_dir = '+'
        else:
            self.angle_dir = '-'

    def draw(self, drawing, color='black'):
        assert color != 'white', 'White arc conductors not yet implemented.'
        path = drawing.path(fill='none', stroke=color, stroke_width=self.width)
        path.push('M', self.start)
        # Note that for our purposes we can assume we're always dealing
        # with the small arc, because there aren't any conductors that are
        # more than 180 degrees wide.
        path.push_arc(self.end, 0, self.radius, large_arc=False, absolute=True,
                      angle_dir=self.angle_dir)
        return path

class ArcConductorWithHook:
    """A conductor that follows an arc segment but also has a hook.

    Angle measurements are in degrees measured from the positive x axis.
    `hook_angle` gives the angle of a line to which the hook is parallel.
    `hook_outer_offset` is the distance from that line to the outer edge
    of the hook.  `hook_length` is measured along the inner edge of the
    hook.  Positive lengths indicate that the hook lies outside the arc,
    and vice versa.

    """
    def __init__(self, width, radius, start_angle, hook_angle, hook_outer_offset, hook_length, hook_width=None):
        self.width = width
        self.radius = radius
        self.start_angle = start_angle / 180 * math.pi
        self.hook_angle = hook_angle / 180 * math.pi
        self.hook_outer_offset = hook_outer_offset
        self.hook_length = hook_length
        if hook_width is None:
            self.hook_width = width
        else:
            self.hook_width = hook_width
        self.hook_width = math.copysign(self.hook_width, hook_outer_offset)

    def draw(self, drawing, color='black'):
        outer_radius = self.radius + self.width/2
        inner_radius = self.radius - self.width/2
        
        start_inner = cmath.rect(inner_radius, self.start_angle)
        start_outer = cmath.rect(outer_radius, self.start_angle)

        angle_to_end_outer = math.asin(self.hook_outer_offset / outer_radius)
        end_outer = cmath.rect(outer_radius, self.hook_angle + angle_to_end_outer)
        angle_to_end_inner = math.asin((self.hook_outer_offset - self.hook_width) / inner_radius)
        end_inner = cmath.rect(inner_radius, self.hook_angle + angle_to_end_inner)
        if self.hook_length < 0:
            vector_to_hook_inner_corner = cmath.rect(self.hook_length, self.hook_angle)
            hook_inner_corner = end_inner + vector_to_hook_inner_corner
            vector_to_hook_outer_corner = cmath.rect(self.hook_width, self.hook_angle + math.pi / 2)
            hook_outer_corner = hook_inner_corner + vector_to_hook_outer_corner
        else:
            assert False
            
        path = drawing.path(fill=color)
        if color == 'white':
            path['stroke'] = 'black'
            path['stroke-width'] = OUTLINE_WIDTH
        path.push('M', (start_outer.real, start_outer.imag))
        path.push_arc((end_outer.real, end_outer.imag), 0, outer_radius,
                      large_arc=False, absolute=True,
                      angle_dir='+' if self.hook_outer_offset > 0 else '-')
        if self.hook_length < 0:
            path.push('L', (hook_outer_corner.real, hook_outer_corner.imag))
            path.push('L', (hook_inner_corner.real, hook_inner_corner.imag))
        else:
            assert False
        path.push('L', (end_inner.real, end_inner.imag))
        path.push_arc((start_inner.real, start_inner.imag), 0, inner_radius,
                      large_arc=False, absolute=True,
                      angle_dir='-' if self.hook_outer_offset > 0 else '+')
        path.push('Z')

        return path
