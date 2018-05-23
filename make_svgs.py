#!/usr/bin/env python3

# All dimensions based on ANSI/NEMA WD 6-2016
#
# For receptacles, the slot outlines match the *minimum* dimensions given
# in the standard.  For plugs, the prong outlines match the *maximum*
# dimensions given.
#
# The circles around the connectors are sized according to the dimensions
# for flanged inlets and connector bodies on page 16.

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

if __name__ == '__main__':
    NEMA_1_15().save()
    NEMA_1_20().save()
    NEMA_5_15().save()
    NEMA_5_20().save()
    
