import cadquery as cq
import math

# shell thickness
th = 1.5
# shell fillet radius
fillet_r = 1.5

centerXY = (True, True, False)

wart_depth = 15
wart_width = 20
height = 45
width = 40
depth = 15

# make shell
result = (cq.Workplane("XZ")
          .hLine(width)
          .vLine(height - wart_depth)
          .hLine(-wart_width)
          .vLine(wart_depth)
          .hLine(-(width - wart_width))
          .lineTo(0, 0)
          .close()
          .extrude(depth)
          .shell(-th)
          # round back edges
          #.edges(">Z").fillet(fillet_r)
          # round top
          .faces("")
          .edges().fillet(fillet_r)
          )

result.faces("<Z").workplane(centerOption="CenterOfMass", 
                             invert=True).tag("end")
result.faces("<Y").workplane(centerOption="CenterOfMass", 
                             invert=True).tag("bot")

result = (result
          .workplaneFromTagged("bot")
          .circle(3)
          .extrude(depth)
          .workplaneFromTagged("bot")
          .circle(0.7)
          .cutBlind(depth/2)
          .workplaneFromTagged("bot")
          .circle(3.7/2)
          .cutBlind(th)
          .workplaneFromTagged("bot")
          .circle(2/2)
          .cutBlind(2*th)
          
          )

# DC socket hole
result = (result
          .workplaneFromTagged("end")
          .transformed(offset=(width/2-wart_width/2-10, 0, height-wart_depth*0.5), rotate=(0, 90, 0))
          .circle(4)
          .cutBlind(-10)
          )

# LED wire hole
result = (result
          .workplaneFromTagged("end")
          .transformed(offset=(0, 0, 0), rotate=(0, 0, 0))
          .slot2D(3, 1.5)
          .cutBlind(10)
          )

# USB power hole
result = (result
          .workplaneFromTagged("end")
          .transformed(offset=(0, 0, 8), rotate=(0, 90, 0))
          .circle(3.5/2)
          .cutBlind(-width/2)
          )

cut_h = depth - 2*th
p1 = result.faces(">Y").workplane(-cut_h).split(keepTop=True)

p2 = result.faces(">Y").workplane(-cut_h).split(keepBottom=True)

#show_object(p1)
show_object(p2)
