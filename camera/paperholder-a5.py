import cadquery as cq
import math

fillet_r = 1.5

centerXY = (True, True, False)

height = 3
thickness = 12
iw = 145 - 2 * thickness
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
          .workplaneFromTagged("o")
          .transformed(offset=(0, 0, -height/2+0.75))
          .rarray(ow, 1, 2, 1)
          .rect(5, iw*0.75)
          .cutBlind(-10)
          .workplaneFromTagged("o")
          .transformed(offset=(0, 0, -height/2+0.75))
          .rarray(1, ow, 1, 2)
          .rect(iw*0.75, 5)
          .cutBlind(-10)
          )
show_object(result)
