from math import radians, sin, cos, sqrt, asin

'''
    Based on the formula derived by James Andrew in 1805. Code referenced 
    from https://rosettacode.org/wiki/Haversine_formula. 
    
    Given two sets of coordinates, find the distance between them, taking
    into account the spherical nature of the earth. 
    
'''
class Haversine():
    def calculate_distance(lat1, lon1, lat2, lon2):
        R = 3963.1676  # Earth radius in miles

        dLat = radians(lat2 - lat1)
        dLon = radians(lon2 - lon1)
        lat1 = radians(lat1)
        lat2 = radians(lat2)

        a = sin(dLat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dLon / 2) ** 2
        c = 2 * asin(sqrt(a))

        return R * c