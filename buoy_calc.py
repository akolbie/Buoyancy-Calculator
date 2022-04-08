"""
Calculates the location of the center of 
gravity and center of buoyancy for a 1D vessel.

Vessel location is measured from the bottom of the vehicle to the bottom of the vessel
Vessel COG and COB is measured from the bottom of the vessel up
Water height is measured 
"""

from cmath import pi, sqrt
import csv
from math import acos
from turtle import circle

WATER_DENSITY = 1000 #KG/M^3
GRAVITY = 9.81 #M/S^2

FOAM_DENSITY = 288 #kg/m^3
FOAM_IN_WATER_BUOYANCY = WATER_DENSITY - FOAM_DENSITY
WEIGHT_DENSITY = 7500 #kg/m^3
WEIGHT_IN_WATER_WEIGHT = WEIGHT_DENSITY - WATER_DENSITY


class Vessel():
    """
    Defines any item adding contributing to the
    vehicles mass and buoyancy
    """
    def __init__(self, name, weight, COG, COB, buoyancy, height, radius):
        self.name = name
        self.weight = weight
        self.buoyancy = buoyancy
        self.COG = COG
        self.COB = COB
        self.height = height
        self.radius = radius
    
    def buoyancy_at_point(self, position, vessel_location):
        if position > vessel_location + self.height:
            return self.buoyancy, self.COB
        elif position < vessel_location:
            return 0, 0
        elif not self.radius:
            precent = (position - vessel_location) / self.height
        else: # circular
            h = position - vessel_location
            if h > self.radius: #more than halfway up the circle
                h -= self.radius
                precent = 1 - self.circle_area_precent(h)
            else:
                precent = self.circle_area_precent(h)
        mod_buoyancy = self.buoyancy * precent
        mod_COB = self.COB * precent
        return mod_buoyancy, mod_COB
                
    def circle_area_precent(self, h):
        total_area = pi * self.radius ** 2
        sliver_area = self.radius ** 2 * acos((self.radius - h) / self.radius)
        sliver_area -= (self.radius - h) * sqrt(2 * self.radius * h - h ** 2)
        return sliver_area / total_area


class SideWall(Vessel):
    """
    Sub-class of vessel, specifically for the vertical 
    walls of the vessel, to allow smoother waterline calcs
    """
    def __init__(self, name, weight, COG, COB, buoyancy, height, radius):
        super().__init__(name, weight, COG, COB, buoyancy, height, radius)

    def buoyancy_at_point(self, position):
        if position > self.height:
            return self.buoyancy, self.COB
        precent = self.height / position
        mod_COB = self.COB * precent
        mod_buoyancy = self.buoyancy * precent
        return mod_buoyancy, mod_COB
        

class Vehicle():
    """
    A class which is the combination of vessels and
    some additional parameters to define a vehicle
    """
    def __init__(self, vehicle_height, water_height):
        self.water_height = water_height
        self.height = vehicle_height
        self.weight = 0
        self.vessels = []
        self.side_walls = []
        self.buoyancy = 0
        self.net_force = 0
    
    def add_vessel(self, vessel, location):
        self.vessels.append({'vessel' : vessel, 'location' : location})
        self.weight += vessel.weight
    
    def add_side_wall(self, wall, location = 0):
        self.side_walls.append({'wall' : wall, 'location' : location})
        self.weight += wall.weight

    def calc_center_of_gravity(self):
        self.COG = 0
        for vessel in self.vessels:
            self.COG += (vessel['vessel'].COG + vessel['location']) * vessel['vessel'].weight
        for wall in self.side_walls:
            self.COG += (wall['wall'].COG + wall['location']) * wall['wall'].weight
        self.COG /= self.weight
    
    def calc_center_of_buoyancy(self):
        self.COB = 0
        self.buoyancy = 0
        for vessel in self.vessels:
            temp_buoy, temp_COB = vessel['vessel'].bouyancy_at_point(self.water_height ,vessel['location'])
            self.buoyancy += temp_buoy
            self.COB += temp_COB
                
        for wall in self.side_walls:
            temp_buoy, temp_COB = wall.buoyancy_at_point(self.water_height)
            self.COB += temp_buoy * temp_COB
            self.buoyancy += temp_buoy
        self.COB /= self.buoyancy

    def calc_net_force(self):
        self.calc_net_force = self.buoyancy - self.weight

    def recalc(self):
        self.calc_center_of_gravity()
        self.calc_center_of_buoyancy()

    def calc_water_height(self):
        buoyancy = 0
        waterline_found = False
        self.vessels.sort(key = lambda x: x['location'])
        for vessel in self.vessels:
            if vessel['vessel'].buoyancy + buoyancy < self.weight:
                buoyancy += vessel['vessel'].buoyancy
            elif vessel['vessel'].bouyancy + buoyancy > self.weight:
                left_weight = self.weight - buoyancy
                precent = left_weight / vessel['vessel'].buoyancy
                self.calced_water_height = vessel['location'] + vessel['vessel'].height * precent
                waterline_found = True
                break
            else:
                self.calced_water_height = vessel['location'] + vessel['vessel'].height 
                waterline_found = True
                break
        if not waterline_found:
            print('Add foam')

    def calc_COG_COB_distance(self):
        return self.COB - self.COG       

class Vessel_Comparison():
    """
    A class for comparing two identical vehicles with 
    a full vs empty buoyancy engine
    """
    def __init__(self, empty_vehicle, full_vehicle):
        self.empty_vehicle = empty_vehicle
        self.full_vehicle = full_vehicle
    
    def calc_foam_or_weight(self):
        difference = self.full_vehicle.net_force - self.empty_vehicle.net_force

        if difference > 0: # add weight
            amount = difference / WEIGHT_IN_WATER_WEIGHT
            self.empty_vehicle.add_vessel(Vessel(WEIGHT_DENSITY * abs(amount), amount, 1, 1, 2), 0)
            self.full_vehicle.add_vessel(Vessel(WEIGHT_DENSITY * abs(amount), amount, 1, 1, 2), 0)
        elif difference < 0: # add foam
            amount = difference / FOAM_IN_WATER_BUOYANCY
            self.empty_vehicle.add_vessel(Vessel(FOAM_DENSITY * abs(amount), amount,1, 1, 2), self.empty_vehicle.height)
            self.full_vehicle.add_vessel(Vessel(FOAM_DENSITY * abs(amount), amount,1, 1, 2), self.full_vehicle.height)
        else:
            amount = 0
        
        self.empty_vehicle.recalc()
        self.full_vehicle.recalc()
        return amount, self.empty_vehicle.vessels[-1].weight # maybe just pass the vessel?

def split_csv_row(row):
    return [
        row[0],
        *row[2:8],
        row[8:]
    ]

def import_data(location):
    """
    Returns a list of vessel objects
    """
    vessel = []
    walls = []
    varying_vessel = []
    
    vessel_flag = True
    vehicle_height_flag = False
    with open(location, "r") as f:
        csv_reader = csv.reader(f)
        for i, row in csv_reader:
            if i == 0:
                continue
            elif row[0] == "0":
                vessel_flag = False
                continue
            elif vessel_flag:
                if row[1] == "Module":
                    vessel.append(split_csv_row(row))
                elif row[1] == "Wall":
                    walls.append(split_csv_row(row))
                else:
                    varying_vessel.append(split_csv_row(row))
            else:
                if not vehicle_height_flag:
                    vehicle_height = row[1]
                    vehicle_height_flag = True
                else:
                    water_height = row[1]
    return vessel, walls, varying_vessel, vehicle_height, water_height

if __name__ == '__main__':
    vessels, walls, varying_vessels, vehicle_height, water_height = import_data('data.csv')

    #multiple_vehicles(vessels, heights, vehicle_data)
    #vehicle_comparisons(vessels, heights, vehicle_data)


