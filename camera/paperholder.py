import cadquery as cq
import math

fillet_r = 1.5

centerXY = (True, True, False)

height = 7
width = 92
thickness = 9
mcc = width - thickness - 2
result = (cq.Workplane("XY")
          .tag("o")
          .box(width, width, height)
          .workplaneFromTagged("o")
          .rect(width - 2*thickness, width - 2*thickness)
          .cutThruAll()
          .edges("|Z")
          .fillet(2)
          .faces(">Z")
          .fillet(1)
          .workplaneFromTagged("o")
          .transformed(offset=(0, 0, -height/2+1))
          .rarray(mcc, mcc, 2, 2)
          .circle(6.5/2)
          .cutBlind(10)
          )
show_object(result)
