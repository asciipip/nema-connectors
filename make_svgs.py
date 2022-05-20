#!/usr/bin/env python3

# All dimensions based on ANSI/NEMA WD 6-2016
#
# For receptacles, the slot outlines match the *minimum* dimensions given
# in the standard.  For plugs, the prong outlines match the *maximum*
# dimensions given.
#
# The circles around the connectors are sized according to the dimensions
# for flanged inlets and connector bodies on page 16.

from enum import Enum

import svgwrite

import conductors


OUTLINE_WIDTH = 0.01

class ConductorType(Enum):
    ground = 'Ground'
    neutral = 'Neutral'
    lineX = 'Line (X)'
    lineY = 'Line (Y)'
    lineZ = 'Line (Z)'

CONDUCTOR_COLORS = {
    ConductorType.ground: 'green',
    ConductorType.neutral: 'gray',
    ConductorType.lineX: 'black',
    ConductorType.lineY: 'red',
    ConductorType.lineZ: 'blue',
}
    
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
        
        for ctype, conductor in conductors.items():
            g.add(conductor.draw(drawing, CONDUCTOR_COLORS[ctype]))
        
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
                conductors.IConductor(slot_width, neutral_slot_height, x=conductor_spacing/2),
                conductors.IConductor(prong_width, neutral_prong_height, x=-conductor_spacing/2)
            ),
            ConductorType.lineX: (
                conductors.IConductor(slot_width, line_slot_height, x=-conductor_spacing/2),
                conductors.IConductor(prong_width, line_prong_height, x=conductor_spacing/2)
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
                conductors.LConductor(prong_width, neutral_start, neutral_end, '+'),
            ),
            ConductorType.lineX: (
                None,
                conductors.IConductor(prong_width, line_height, x=conductor_spacing/2),
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
                conductors.IConductor(slot_width, neutral_slot_height,
                                      x=conductor_spacing/2, y=lower_offset),
                conductors.IConductor(prong_width, neutral_prong_height,
                                      x=-conductor_spacing/2, y=lower_offset)
            ),
            ConductorType.ground: (
                conductors.DConductor(ground_slot_dims, ground_slot_dims,
                                      y=lower_offset - upper_offset, rotation=90),
                conductors.OConductor(ground_prong_dims, y=lower_offset - upper_offset),
            ),
            ConductorType.lineX: (
                conductors.IConductor(slot_width, line_slot_height,
                                      x=-conductor_spacing/2, y=lower_offset),
                conductors.IConductor(prong_width, line_prong_height,
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
                conductors.TConductor(slot_width, neutral_slot_height, neutral_slot_width,
                                      x=receptacle_conductor_spacing/2, y=lower_offset,
                                      rotation=90),
                conductors.IConductor(prong_length, prong_width, y=lower_offset,
                                      x=plug_line_offset - plug_neutral_offset)
            ),
            ConductorType.ground: (
                conductors.DConductor(ground_slot_dims, ground_slot_dims,
                                      y=lower_offset - upper_offset, rotation=90),
                conductors.OConductor(ground_prong_dims, y=lower_offset - upper_offset),
            ),
            ConductorType.lineX: (
                conductors.IConductor(slot_width, line_slot_height,
                                      x=-receptacle_conductor_spacing/2, y=lower_offset),
                conductors.IConductor(prong_width, prong_length,
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
                conductors.ArcConductor(slot_width, conductor_radius,
                                        neutral_angle_slot_end - 180,
                                        neutral_angle_slot_end - neutral_angle_slot_width - 180),
                conductors.ArcConductor(prong_width, conductor_radius,
                                        0 - neutral_angle_prong_end,
                                        0 - neutral_angle_prong_end + neutral_angle_prong_width),
            ),
            ConductorType.ground: (
                conductors.ArcConductorWithHook(slot_width, conductor_radius,
                                                ground_angle_slot_start - 180, -180,
                                                ground_hook_slot_outer_y,
                                                -ground_hook_slot_width,
                                                ground_hook_slot_height),
                conductors.ArcConductorWithHook(prong_width, conductor_radius,
                                                -ground_angle_prong_start, 0,
                                                -ground_hook_prong_outer_y,
                                                -ground_hook_prong_width,
                                                ground_hook_prong_height),
            ),
            ConductorType.lineX: (
                conductors.ArcConductor(slot_width, conductor_radius,
                                        line_angle_slot_end - 180,
                                        line_angle_slot_end - line_angle_slot_width - 180),
                conductors.ArcConductor(prong_width, conductor_radius,
                                        0 - line_angle_prong_end,
                                        0 - line_angle_prong_end + line_angle_prong_width),
            ),
        }

class NEMA_L6_20(NEMABase):
    def __init__(self):
        super().__init__()
        
        self.name = 'L6-20'

        self.receptacle_diameter = 1.860
        self.plug_diameter = 1.880

        conductor_radius = 0.437
        slot_width = 0.075
        prong_width = 0.060

        line1_angle_slot_end = 152
        line1_angle_slot_width = 57
        line2_angle_slot_end = 262
        line2_angle_slot_width = 42.5

        ground_angle_slot_start = -25
        ground_hook_slot_outer_y = 0.220
        ground_hook_slot_height = 0.100
        ground_hook_slot_width = 0.105

        line1_angle_prong_end = 149.5
        line1_angle_prong_width = 52.5
        line2_angle_prong_end = 259.5
        line2_angle_prong_width = 38

        ground_angle_prong_start = -22.5
        ground_hook_prong_outer_y = 0.200
        ground_hook_prong_height = prong_width
        ground_hook_prong_width = 0.094
        
        self.conductors = {
            ConductorType.lineX: (
                conductors.ArcConductor(slot_width, conductor_radius,
                                        line1_angle_slot_end - 180,
                                        line1_angle_slot_end - line1_angle_slot_width - 180),
                conductors.ArcConductor(prong_width, conductor_radius,
                                        0 - line1_angle_prong_end,
                                        0 - line1_angle_prong_end + line1_angle_prong_width),
            ),
            ConductorType.ground: (
                conductors.ArcConductorWithHook(slot_width, conductor_radius,
                                                ground_angle_slot_start - 180, -180,
                                                ground_hook_slot_outer_y,
                                                -ground_hook_slot_width,
                                                ground_hook_slot_height),
                conductors.ArcConductorWithHook(prong_width, conductor_radius,
                                                -ground_angle_prong_start, 0,
                                                -ground_hook_prong_outer_y,
                                                -ground_hook_prong_width,
                                                ground_hook_prong_height),
            ),
            ConductorType.lineY: (
                conductors.ArcConductor(slot_width, conductor_radius,
                                        line2_angle_slot_end - 180,
                                        line2_angle_slot_end - line2_angle_slot_width - 180),
                conductors.ArcConductor(prong_width, conductor_radius,
                                        0 - line2_angle_prong_end,
                                        0 - line2_angle_prong_end + line2_angle_prong_width),
            ),
        }

if __name__ == '__main__':
    NEMA_1_15().save()
    NEMA_1_20().save()
    NEMA_5_15().save()
    NEMA_5_20().save()
    NEMA_L5_30().save()
    NEMA_L6_20().save()
