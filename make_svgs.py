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

class NEMA_1_15:
    def __init__(self):
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

    def draw(self, diameter, conductors):
        drawing_width = diameter + OUTLINE_WIDTH * 2
        drawing = svgwrite.Drawing(size=(round(drawing_width * SCALE + 0.5),
                                         round(drawing_width * SCALE + 0.5)),
                                   viewBox='0 0 {0} {0}'.format(drawing_width))
        g = drawing.g(transform='translate({0} {0})'.format(drawing_width / 2))
        drawing.add(g)

        g.add(drawing.circle(r=diameter/2, fill='white', stroke='black',
                             stroke_width=OUTLINE_WIDTH))
        for conductor in conductors.values():
            g.add(conductor.draw(drawing))
        
        return drawing
        
    def draw_receptacle(self):
        return self.draw(self.receptacle_diameter, {k: v[0] for k, v in self.conductors.items()})

    def draw_plug(self):
        return self.draw(self.plug_diameter, {k: v[1] for k, v in self.conductors.items()})

    def save(self):
        self.draw_receptacle().saveas('NEMA_{}R.svg'.format(self.name))
        self.draw_plug().saveas('NEMA_{}P.svg'.format(self.name))
        
if __name__ == '__main__':
    NEMA_1_15().save()
    
