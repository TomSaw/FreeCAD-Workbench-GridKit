import FreeCAD

def vecCompDiv(v1, v2):
    v = FreeCAD.Vector()
    v.x = v1.x / v2.x
    v.y = v1.y / v2.y
    v.z = v1.z / v2.z
    return v