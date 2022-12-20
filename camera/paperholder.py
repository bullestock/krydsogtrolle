import cadquery as cq
import math

fillet_r = 1.5

centerXY = (True, True, False)

height = 3
iw = 80
width = 92
thickness = 12
ow = iw + 2*thickness
mcc = (iw + ow)/2 - 2
result = (cq.Workplane("XY")
          .tag("o")
          .box(ow, ow, height)
          .workplaneFromTagged("o")
          .rect(iw, iw)
          .cutThruAll()
          .edges("|Z")
          .fillet(2)
          .faces(">Z")
          .fillet(1)
          .workplaneFromTagged("o")
          .transformed(offset=(0, 0, -height/2+0.12))
          .rarray(mcc, mcc, 2, 2)
          .circle(10.2/2)
          .cutBlind(10)
          )
show_object(result)
