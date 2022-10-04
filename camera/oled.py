import cadquery as cq
import math

# shell thickness
th = 1.5
# shell fillet radius
fillet_r = 1.5

centerXY = (True, True, False)

height = 10
width = 45
depth = 17
slot_w = 3.5

# make shell
result = (cq.Workplane("XY")
          .tag("o")
          .box(width, depth, height)
          .shell(-th)
          .faces("")
          .edges().fillet(fillet_r)
          .workplaneFromTagged("o")
          .rect(25, 10)
          .cutBlind(height)
          .workplaneFromTagged("o")
          .transformed(offset=((width - 3*slot_w)/2, 0, 0))
          .rect(slot_w, 12)
          .cutBlind(-height)
          )

cut_h = 0
p1 = (result
     .workplaneFromTagged("o")
     .workplane(cut_h)
     .split(keepBottom=True)
     )

show_object(p1)
