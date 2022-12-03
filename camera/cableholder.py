import cadquery as cq
import math

cc = 10
height = 5
depth = 7
d1 = 4.8
d2 = 3.25
d3 = 3.8

def slot(o, offset, dia):
    return (o
            .workplaneFromTagged("o")
            .transformed(offset=(offset, 0, 0))
            .circle(dia/2)
            .cutThruAll()
            .workplaneFromTagged("o")
            .transformed(offset=(offset, -depth/2, 0))
            .rect(dia*0.9, depth)
            .cutThruAll()
            )

result = (cq.Workplane("XY")
          .tag("o")
          .box(3*cc, depth, height)
          #.edges("<Y")
          #.fillet(1)
          )

result = slot(result, -cc, d1)
result = slot(result, 0, d2)
result = slot(result, cc, d3)

result = (result
          .edges("<Y")
          .fillet(0.5)
          .edges("(>Z or <Z)")
          .fillet(0.25)
          )