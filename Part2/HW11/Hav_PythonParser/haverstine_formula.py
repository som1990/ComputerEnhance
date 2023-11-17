import typing as t
import math as m

def Square(A: float)->float:
    return A*A

def RadiansFromDegrees(Degrees: float)->float:
    return 0.01745329251994329577 * Degrees
    
def ReferenceHaversine(x0: float, y0: float, x1: float, y1: float, earth_radius: float)->float:

    lat1 = y0
    lat2 = y1
    lon1 = x0
    lon2 = x1

    dLat: float = RadiansFromDegrees(lat2-lat1)
    dLon: float = RadiansFromDegrees(lon2-lon1)
    lat1: float = RadiansFromDegrees(lat1)
    lat2: float = RadiansFromDegrees(lat2)

    a: float = Square(m.sin(dLat/2.0) + m.cos(lat1)*m.cos(lat2)*Square(m.sin(dLon/2.0)))
    c: float = 2.0 * m.asin(m.sqrt(a))

    result: float = earth_radius * c

    return result

