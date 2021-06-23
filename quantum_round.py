import math

# Round in Quantum Steps
def qround(x, q):
    return round(x / q) * q

def qceil(x, q):
    return math.ceil(x / q) * q

def qfloor(x, q):
    return math.floor(x / q) * q