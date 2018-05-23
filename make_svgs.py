#!/usr/bin/env python3

# All dimensions based on ANSI/NEMA WD 6-2016
#
# For receptacles, the slot outlines match the *minimum* dimensions given
# in the standard.  For plugs, the prong outlines match the *maximum*
# dimensions given.
#
# The circles around the connectors are sized according to the dimensions
# for flanged inlets and connector bodies on page 16.

import cmath
import math
from enum import Enum

import svgwrite

OUTLINE_WIDTH = 0.01

class ConductorType(Enum):
    ground = 'Ground'
    neutral = 'Neutral'
    lineX = 'Line (X)'
    lineY = 'Line (Y)'
    lineZ = 'Line (Z)'

class DConductor:
    """A conductor whose outline forms a "D" shape.

    The curve of the "D" is done at the positive end of the narrowest
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

    def draw(self, drawing):
        path = drawing.path(fill='black')
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

    def draw(self, drawing):
        return drawing.rect((self.x - self.width/2, self.y - self.height/2),
                            (self.width, self.height),
                            fill='black')

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

    def draw(self, drawing):
        path = drawing.path(fill='none', stroke='black', stroke_width=self.width)
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

    def draw(self, drawing):
        return drawing.circle((self.x, self.y), self.radius, fill='black')

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

    def draw(self, drawing):
        path = drawing.path(fill='none', stroke='black', stroke_width=self.width)
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

    def draw(self, drawing):
        path = drawing.path(fill='none', stroke='black', stroke_width=self.width)
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

    def draw(self, drawing):
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
            
        path = drawing.path(fill='black')
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
    
class NEMABase:
    def __init__(self):
        self.receptacle_diameter = None
        self.plug_diameter = None
        
    def draw(self, diameter, conductors, outline):
        drawing_width = diameter + OUTLINE_WIDTH * 2
        dim_str = '{}in'.format(drawing_width)
        drawing = svgwrite.Drawing(size=(dim_str, dim_str),
                                   viewBox='0 0 {0} {0}'.format(drawing_width))
        g = drawing.g(transform='translate({0} {0})'.format(drawing_width / 2))
        drawing.add(g)

        background = drawing.circle(r=diameter/2, fill='white')
        if outline:
            background['stroke'] = 'black'
            background['stroke-width'] = OUTLINE_WIDTH
        g.add(background)
        
        for conductor in conductors.values():
            g.add(conductor.draw(drawing))
        
        return drawing
        
    def draw_receptacle(self):
        if self.receptacle_diameter is None:
            return None
        else:
            return self.draw(self.receptacle_diameter,
                             {k: v[0] for k, v in self.conductors.items()},
                             True)

    def draw_plug(self):
        if self.plug_diameter is None:
            return None
        else:
            return self.draw(self.plug_diameter,
                             {k: v[1] for k, v in self.conductors.items()},
                             False)

    def save(self):
        if self.receptacle_diameter is not None:
            self.draw_receptacle().saveas('NEMA_{}R.svg'.format(self.name))
        if self.plug_diameter is not None:
            self.draw_plug().saveas('NEMA_{}P.svg'.format(self.name))

class NEMA_1_15(NEMABase):
    def __init__(self):
        super().__init__()
        
        self.name = '1-15'

        self.receptacle_diameter = 1.531
        self.plug_diameter = 1.550
        
        conductor_spacing = 0.500
        
        slot_width = 0.075
        neutral_slot_height = 0.330
        line_slot_height = 0.265

        prong_width = 0.060
        neutral_prong_height = 0.322
        line_prong_height = 0.260
        
        self.conductors = {
            ConductorType.neutral: (
                IConductor(slot_width, neutral_slot_height, x=conductor_spacing/2),
                IConductor(prong_width, neutral_prong_height, x=-conductor_spacing/2)
            ),
            ConductorType.lineX: (
                IConductor(slot_width, line_slot_height, x=-conductor_spacing/2),
                IConductor(prong_width, line_prong_height, x=conductor_spacing/2)
            ),
        }

class NEMA_1_20(NEMABase):
    def __init__(self):
        super().__init__()
        
        self.name = '1-20'

        self.plug_diameter = 1.550
        
        conductor_spacing = 0.500

        prong_width = 0.060
        neutral_width = 0.260
        neutral_height = 0.165
        line_height = 0.260

        neutral_start = (0 - conductor_spacing/2 - (neutral_width - prong_width/2), 0)
        neutral_end = (0 - conductor_spacing/2, 0 + (neutral_height - prong_width/2))
        self.conductors = {
            ConductorType.neutral: (
                None,
                LConductor(prong_width, neutral_start, neutral_end, '+'),
            ),
            ConductorType.lineX: (
                None,
                IConductor(prong_width, line_height, x=conductor_spacing/2),
            ),
        }

class NEMA_5_15(NEMABase):
    def __init__(self):
        super().__init__()
        
        self.name = '5-15'

        self.receptacle_diameter = 1.531
        self.plug_diameter = 1.550
        
        conductor_spacing = 0.500
        lower_offset = 0.125
        upper_offset = 0.468
        
        slot_width = 0.075
        neutral_slot_height = 0.330
        line_slot_height = 0.265
        ground_slot_dims = 0.205

        prong_width = 0.060
        neutral_prong_height = 0.322
        line_prong_height = 0.260
        ground_prong_dims = 0.190
        
        self.conductors = {
            ConductorType.neutral: (
                IConductor(slot_width, neutral_slot_height,
                           x=conductor_spacing/2, y=lower_offset),
                IConductor(prong_width, neutral_prong_height,
                           x=-conductor_spacing/2, y=lower_offset)
            ),
            ConductorType.ground: (
                DConductor(ground_slot_dims, ground_slot_dims,
                           y=lower_offset - upper_offset, rotation=90),
                OConductor(ground_prong_dims, y=lower_offset - upper_offset),
            ),
            ConductorType.lineX: (
                IConductor(slot_width, line_slot_height,
                           x=-conductor_spacing/2, y=lower_offset),
                IConductor(prong_width, line_prong_height,
                           x=conductor_spacing/2, y=lower_offset)
            ),
        }

class NEMA_5_20(NEMABase):
    def __init__(self):
        super().__init__()
        
        self.name = '5-20'

        self.receptacle_diameter = 1.531
        self.plug_diameter = 1.550
        
        receptacle_conductor_spacing = 0.500
        plug_line_offset = 0.250
        plug_neutral_offset = 0.609
        lower_offset = 0.125
        upper_offset = 0.468
        
        slot_width = 0.075
        neutral_slot_height = 0.330
        neutral_slot_width = 0.290
        line_slot_height = 0.265
        ground_slot_dims = 0.205

        prong_width = 0.060
        prong_length = 0.260
        ground_prong_dims = 0.190
        
        self.conductors = {
            ConductorType.neutral: (
                TConductor(slot_width, neutral_slot_height, neutral_slot_width,
                           x=receptacle_conductor_spacing/2, y=lower_offset,
                           rotation=90),
                IConductor(prong_length, prong_width, y=lower_offset,
                           x=plug_line_offset - plug_neutral_offset)
            ),
            ConductorType.ground: (
                DConductor(ground_slot_dims, ground_slot_dims,
                           y=lower_offset - upper_offset, rotation=90),
                OConductor(ground_prong_dims, y=lower_offset - upper_offset),
            ),
            ConductorType.lineX: (
                IConductor(slot_width, line_slot_height,
                           x=-receptacle_conductor_spacing/2, y=lower_offset),
                IConductor(prong_width, prong_length,
                           x=plug_line_offset, y=lower_offset)
            ),
        }

class NEMA_L5_30(NEMABase):
    def __init__(self):
        super().__init__()
        
        self.name = 'L5-30'

        self.receptacle_diameter = 1.860
        self.plug_diameter = 1.880

        conductor_radius = 0.500
        slot_width = 0.093
        prong_width = 0.070

        neutral_angle_slot_end = 127
        neutral_angle_slot_width = 42.5
        line_angle_slot_end = 242
        line_angle_slot_width = 52

        ground_angle_slot_start = -25
        ground_hook_slot_outer_y = 0.248
        ground_hook_slot_height = 0.114
        ground_hook_slot_width = 0.105

        neutral_angle_prong_end = 124.5
        neutral_angle_prong_width = 38
        line_angle_prong_end = 239.5
        line_angle_prong_width = 47.5

        ground_angle_prong_start = -22.5
        ground_hook_prong_outer_y = 0.220
        ground_hook_prong_height = prong_width
        ground_hook_prong_width = 0.100
        
        self.conductors = {
            ConductorType.neutral: (
                ArcConductor(slot_width, conductor_radius,
                             neutral_angle_slot_end - 180,
                             neutral_angle_slot_end - neutral_angle_slot_width - 180),
                ArcConductor(prong_width, conductor_radius,
                             0 - neutral_angle_prong_end,
                             0 - neutral_angle_prong_end + neutral_angle_prong_width),
            ),
            ConductorType.ground: (
                ArcConductorWithHook(slot_width, conductor_radius,
                                     ground_angle_slot_start - 180, -180,
                                     ground_hook_slot_outer_y,
                                     -ground_hook_slot_width,
                                     ground_hook_slot_height),
                ArcConductorWithHook(prong_width, conductor_radius,
                                     -ground_angle_prong_start, 0,
                                     -ground_hook_prong_outer_y,
                                     -ground_hook_prong_width,
                                     ground_hook_prong_height),
            ),
            ConductorType.lineX: (
                ArcConductor(slot_width, conductor_radius,
                             line_angle_slot_end - 180,
                             line_angle_slot_end - line_angle_slot_width - 180),
                ArcConductor(prong_width, conductor_radius,
                             0 - line_angle_prong_end,
                             0 - line_angle_prong_end + line_angle_prong_width),
            ),
        }

if __name__ == '__main__':
    NEMA_1_15().save()
    NEMA_1_20().save()
    NEMA_5_15().save()
    NEMA_5_20().save()
    NEMA_L5_30().save()
