#!/usr/bin/env python3

import math
from enum import Enum

import svgwrite

OUTLINE_WIDTH = 0.01
SCALE = 100

class ConductorType(Enum):
    ground = 'Ground'
    neutral = 'Neutral'
    lineX = 'Line (X)'
    lineY = 'Line (Y)'
    lineZ = 'Line (Z)'

class SquareConductor:
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

class NEMABase:
    def __init__(self):
        self.receptacle_diameter = None
        self.plug_diameter = None
        
    def draw(self, diameter, conductors, outline):
        drawing_width = diameter + OUTLINE_WIDTH * 2
        drawing = svgwrite.Drawing(size=(round(drawing_width * SCALE + 0.5),
                                         round(drawing_width * SCALE + 0.5)),
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
                SquareConductor(slot_width, neutral_slot_height, x=conductor_spacing/2),
                SquareConductor(prong_width, neutral_prong_height, x=-conductor_spacing/2)
            ),
            ConductorType.lineX: (
                SquareConductor(slot_width, line_slot_height, x=-conductor_spacing/2),
                SquareConductor(prong_width, line_prong_height, x=conductor_spacing/2)
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
                SquareConductor(prong_width, line_height, x=conductor_spacing/2),
            ),
        }

if __name__ == '__main__':
    NEMA_1_15().save()
    NEMA_1_20().save()
    
