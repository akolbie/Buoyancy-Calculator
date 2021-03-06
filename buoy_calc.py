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
        self.weight = float(weight)
        self.buoyancy = float(buoyancy)
        self.COG = float(COG)
        self.COB = float(COB)
        self.height = float(height)
        if radius == '':
            self.radius = False
        else:
            self.radius = float(radius)
    
    def buoyancy_at_point(self, position, vessel_location):
        if position > vessel_location + self.height:
            return self.buoyancy, self.COB + vessel_location
        elif position < vessel_location:
            return 0, 0
        elif not self.radius:
            precent = (position - vessel_location) / self.height
        else: # circular
            h = position - vessel_location
            if h > self.radius: #more than halfway up the circle
                h = 2 * self.radius - h
                precent = 1 - self.circle_area_precent(h)
            else:
                precent = self.circle_area_precent(h)
        mod_buoyancy = self.buoyancy * precent
        mod_COB = self.COB * precent
        return mod_buoyancy, mod_COB + vessel_location
                
    def circle_area_precent(self, h):
        total_area = pi * self.radius ** 2
        sliver_area = self.radius ** 2 * acos((self.radius - h) / self.radius)
        sliver_area -= (self.radius - h) * sqrt(2 * self.radius * h - h ** 2)
        return sliver_area.real / total_area

class SideWall(Vessel):
    """
    Sub-class of vessel, specifically for the vertical 
    walls of the vessel, to allow smoother waterline calcs
    """
    def __init__(self, name, weight, COG, COB, buoyancy, height, radius):
        super().__init__(name, weight, COG, COB, buoyancy, height, radius)

    def buoyancy_at_point(self, water_height, position):
        if position > self.height:
            return self.buoyancy, self.COB
        if position == 0:
            return 0, 0
        precent = position / self.height
        mod_COB = self.COB * precent
        mod_buoyancy = self.buoyancy * precent
        return mod_buoyancy, mod_COB

class VaryingVessel(Vessel):
    """
    Sub-class of vessel, specifically for buoyancy engines or hopper weight
    """
    def __init__(self, name, weight, COG, COB, buoyancy, height, radius):
        if "|" in weight:
            if 'opper' in name:
                self.buoyancy_engine = False
                self.weight_empty = float(weight.split('|')[0])
                self.weight_full = float(weight.split('|')[1])
                super().__init__(name, self.weight_empty, COG, COB, buoyancy, height, radius)
            else:
                self.buoyancy_engine = True
                self.weight_empty = float(weight.split('|')[0])
                self.weight_full = float(weight.split('|')[1])
                super().__init__(name, self.weight_empty, COG, COB, buoyancy, height, radius)
        else:
            print("Error neither buoyancy or hopper variable")

    def switch_mode(self):
        if self.weight == self.weight_empty:
            self.weight = self.weight_full
        else:
            self.weight = self.weight_empty
    

class Vehicle():
    """
    A class which is the combination of vessels and
    some additional parameters to define a vehicle
    """
    def __init__(self, name, vehicle_height, water_height, weight_height, buoyancy_height, vehicle_area):
        self.name = name
        self.water_height = float(water_height)
        self.height = float(vehicle_height)
        self.weight = 0
        self.vessels = []
        self.side_walls = []
        self.varying_vessels = []
        self.buoyancy = 0
        self.net_force = 0
        self.weight_height = float(weight_height)
        self.buoyancy_height = float(buoyancy_height)
        self.vehicle_area = float(vehicle_area)
    
    def add_vessel(self, vessel, location):
        self.vessels.append({'vessel' : vessel, 'location' : float(location)})
        self.weight += vessel.weight
        self.recalc()
    
    def add_side_wall(self, wall, location = 0):
        self.side_walls.append({'wall' : wall, 'location' : float(location)})
        self.weight += wall.weight
        self.recalc()
    
    def add_varying_vessel(self, varying_vessel, location):
        if varying_vessel.buoyancy_engine:
            self.varying_vessels.insert(0, {'varying_vessel' : varying_vessel, 'location' : float(location)})
        else:
            self.varying_vessels.append({'varying_vessel' : varying_vessel, 'location' : float(location)})
        self.weight += varying_vessel.weight
        self.recalc()

    def calc_center_of_gravity(self):
        self.COG = 0
        self.weight = 0
        for vessel in self.vessels:
            self.COG += (vessel['vessel'].COG + vessel['location']) * vessel['vessel'].weight
            self.weight += vessel['vessel'].weight
        for wall in self.side_walls:
            self.COG += (wall['wall'].COG + wall['location']) * wall['wall'].weight
            self.weight += wall['wall'].weight
        for varying in self.varying_vessels:
            self.COG += (varying['varying_vessel'].COG + varying['location']) * varying['varying_vessel'].weight
            self.weight += varying['varying_vessel'].weight
        self.COG /= self.weight
    
    def calc_center_of_buoyancy(self, water_height = None):
        self.COB = 0
        self.buoyancy = 0
        if water_height == None:
            water_height = self.water_height 
        for vessel in self.vessels:
            temp_buoy, temp_COB = vessel['vessel'].buoyancy_at_point(water_height, vessel['location'])
            self.buoyancy += temp_buoy
            self.COB += temp_buoy * temp_COB
                
        for wall in self.side_walls:
            temp_buoy, temp_COB = wall['wall'].buoyancy_at_point(water_height, water_height)
            self.COB += temp_buoy * temp_COB
            self.buoyancy += temp_buoy
        
        for varying in self.varying_vessels:
            temp_buoy, temp_COB = varying['varying_vessel'].buoyancy_at_point(water_height, varying['location'])
            self.COB += temp_buoy * temp_COB
            self.buoyancy += temp_buoy
        
        self.COB /= self.buoyancy

    def calc_net_force(self):
        self.net_force = self.buoyancy - self.weight

    def recalc(self, water_height = None):
        self.calc_center_of_gravity()
        self.calc_center_of_buoyancy(water_height)
        self.calc_net_force()

    def calc_water_height(self):
        self.recalc()
        int_height = round(self.height)
        for height in range(int_height):
            buoyancy = 0
            COB = 0
            for vessel in self.vessels:
                temp_buoy, temp_COB = vessel['vessel'].buoyancy_at_point(height, vessel['location'])
                buoyancy += temp_buoy
                COB += temp_buoy * temp_COB
            for wall in self.side_walls:
                temp_buoy, temp_COB = wall['wall'].buoyancy_at_point(None, height)
                buoyancy += temp_buoy
                COB += temp_buoy * temp_COB
            for varying in self.varying_vessels:
                temp_buoy, temp_COB = varying['varying_vessel'].buoyancy_at_point(height, varying['location'])
                buoyancy += temp_buoy
                COB += temp_buoy * temp_COB
            if buoyancy > self.weight:
                return height, buoyancy, COB / buoyancy
        return 6000, buoyancy, COB / buoyancy
    
    def add_buoyancy(self, amount = 0):
        if amount == 0:
            amount = -self.net_force
        if amount < 0:
            self.add_weight(-amount)
            return
        volume = amount / (9.81 * FOAM_IN_WATER_BUOYANCY) #m^3
        weight = volume * FOAM_DENSITY * 9.81
        height = volume * 1000 ** 3 / self.vehicle_area
        buoyancy = volume * WATER_DENSITY * 9.81
        self.add_vessel(
            Vessel('foam_added', weight, height / 2, height / 2, buoyancy, height, ""), 
            self.buoyancy_height)

    def add_weight(self, amount = 0):
        if amount == 0:
            amount = self.net_force
            if amount < 0:
                self.add_buoyancy(-amount)
                return
        volume = amount / (9.81 * WEIGHT_IN_WATER_WEIGHT)
        weight = volume * WEIGHT_DENSITY * 9.81
        buoyancy = volume * WATER_DENSITY * 9.81
        height = volume * 1000 ** 3 / self.vehicle_area
        self.add_vessel(
            Vessel('weight_added', weight, height / 2, height / 2, buoyancy, height, ""),
            self.weight_height
        )


    def calc_COG_COB_distance(self):
        return self.COB - self.COG

    def calc_foam_for_varying(self):
        if len(self.varying_vessels) == 1:
            self.recalc()
            return self.net_force
        else:
            #find net force down
            self.varying_vessels[0]['varying_vessel'].switch_mode() #fill buoyancy engine
            self.recalc()
            force_down = self.net_force

            #find net force up
            self.varying_vessels[0]['varying_vessel'].switch_mode() #empty buoyancy engine
            self.varying_vessels[1]['varying_vessel'].switch_mode() #fill hopper
            self.recalc()
            force_up = self.net_force

            bouyancy_force = - force_down - force_up
            bouyancy_force /= 2

            self.varying_vessels[1]['varying_vessel'].switch_mode() #return to initial state

            return bouyancy_force


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
        csv_reader_temp = csv.reader(f)
        csv_reader = []
        for row in csv_reader_temp:
            csv_reader.append(row)

        for i, row in enumerate(csv_reader):
            if i == 0:
                names  = [*row[8:]]
            elif row[0] == "":
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
                vehicle_height = csv_reader[i][1]
                water_height = csv_reader[i + 1][1]
                weight_height = csv_reader[i + 2][1]
                buoyancy_height = csv_reader[i + 3][1]
                vehicle_area = csv_reader[i + 4][1]
                break

    return names, vessel, walls, varying_vessel, vehicle_height, water_height, weight_height, buoyancy_height, vehicle_area

def output_data(location, vehicles):
    output = []
    for vehicle in vehicles:
        vehicle.recalc()
        if len(vehicle.varying_vessels) == 0: #no hopper or buoyancy engine
            vehicle.add_weight(1000)
            vehicle.add_buoyancy()
            vehicle.add_buoyancy(10)
            vehicle.recalc()
            water, buoy, COB = vehicle.calc_water_height()
            output.append([vehicle.name])
            foam_weight = 0
            weight_weight = 0
            for vessel in vehicle.vessels:
                if vessel['vessel'].name == 'foam_added':
                    foam_weight += vessel['vessel'].weight
                elif vessel['vessel'].name == 'weight_added':
                    weight_weight += vessel['vessel'].weight
            output.append(['Buoyancy Added (mm^3)', foam_weight / (9.81 * FOAM_DENSITY) * 1000 ** 3])
            output.append(["Weight Added (mm^3)", weight_weight / (9.81 * WEIGHT_DENSITY) * 1000 ** 3])
            output.append(['Buoyancy Height (mm)', (foam_weight / (9.81 * FOAM_DENSITY) * 1000 ** 3) / vehicle.vehicle_area])
            output.append(['Out of water height', vehicle.height - water])
            output.append(['Stability', COB - vehicle.COG])
            output.append(['Vehicle Weight (kg)', vehicle.weight / 9.81])
            output.append(['Net Force', buoy - vehicle.weight])
            output.append(["Righting Moment (lbf*ft)", buoy * (COB - vehicle.COG) * 0.738 / 1000])
            output.append([''])
        else: # hopper and / or buoyancy engine
            vehicle.add_buoyancy(vehicle.calc_foam_for_varying())
            vehicle.recalc()
            water, buoy, COB = vehicle.calc_water_height()
            output.append(['',vehicle.name])
            output.append(['Pre launch checks'])
            for i in range(3):
                vehicle.recalc()
                foam_weight = 0
                weight_weight = 0
                for vessel in vehicle.vessels:
                    if vessel['vessel'].name == 'foam_added':
                        foam_weight += vessel['vessel'].weight
                    elif vessel['vessel'].name == 'weight_added':
                        weight_weight += vessel['vessel'].weight
                output.append(['Buoyancy Added (mm^3)', foam_weight / (9.81 * FOAM_DENSITY) * 1000 ** 3])
                output.append(["Weight Added (mm^3)", weight_weight / (9.81 * WEIGHT_DENSITY) * 1000 ** 3])
                output.append(['Buoyancy Height (mm)', (foam_weight / (9.81 * FOAM_DENSITY) * 1000 ** 3) / vehicle.vehicle_area])
                output.append(['Out of water height', vehicle.height - water])
                output.append(['Stability', COB - vehicle.COG])
                output.append(['Vehicle Weight (kg)', vehicle.weight / 9.81])
                output.append(['Net Force', buoy - vehicle.weight])
                output.append(['Net Force', vehicle.net_force])
                output.append(["Righting Moment (lbf*ft)", buoy * (COB - vehicle.COG) * .738 / 1000])
                output.append([''])
                if i == 0:
                    output.append(['Launch'])
                    vehicle.varying_vessels[0]['varying_vessel'].switch_mode()
                elif i == 1:
                    output.append(['Post Nodules'])
                    vehicle.varying_vessels[0]['varying_vessel'].switch_mode()
                    if len(vehicle.varying_vessels) != 1:
                        vehicle.varying_vessels[1]['varying_vessel'].switch_mode()
                else:
                    output.append([''])
                water, buoy, COB = vehicle.calc_water_height()
    
    with open(location, "w+", newline="") as f:
        csv_writer = csv.writer(f)
        for row in output:
            csv_writer.writerow(row)

def build_vehicles(names, vessels, walls, varying_vessels,vehicle_height, water_height, weight_height, buoyancy_height, vehicle_area):
    vehicles = []
    for i in range(len(vessels[0][-1])):
        vehicles.append(Vehicle(names[i],vehicle_height, water_height, weight_height, buoyancy_height, vehicle_area))
        for vessel in vessels:
            if vessel[-1][i] == 'NA':
                continue
            vehicles[-1].add_vessel(Vessel(*vessel[:len(vessel) - 1]), vessel[-1][i])
        for wall in walls:
            if wall[-1][i] == 'NA':
                continue
            vehicles[-1].add_side_wall(SideWall(*wall[:len(wall) - 1]), wall[-1][i])
        for vary_vessel in varying_vessels:
            if vary_vessel[-1][i] == 'NA':
                continue
            vehicles[-1].add_varying_vessel(VaryingVessel(*vary_vessel[:len(vary_vessel) - 1]), vary_vessel[-1][i])
        
        vehicles[-1].recalc()
        vehicles[-1].calc_net_force()
    
    return vehicles
        
if __name__ == '__main__':
    names, vessels, walls, varying_vessels, vehicle_height, water_height, weight_height, buoyancy_height, vehicle_area = import_data('data.csv')
    #vessels, walls, varying_vessels, vehicle_height, water_height, weight_height, buoyancy_height, vehicle_area = import_data('Model Validation.csv')
    vehicles = build_vehicles(names, vessels, walls, varying_vessels, vehicle_height, water_height, weight_height, buoyancy_height, vehicle_area)

    # for vehicle in vehicles:
    #     vehicle.recalc()
    #     #vehicle.add_buoyancy(311)
    #     vehicle.add_buoyancy()
    #     water,buoy,COB = vehicle.calc_water_height()
    #     print(f"{vehicle.name} - Full buoyancy engine, empty hopper")
    #     print(f'Water height {water}, stability {COB - vehicle.COG}, net_force {vehicle.net_force} fully submerged, vehicle weight {vehicle.weight / 9.81}')
    #     vehicle.varying_vessels[0]['varying_vessel'].switch_mode()
    #     vehicle.varying_vessels[1]['varying_vessel'].switch_mode()
    #     vehicle.recalc()
    #     water,buoy,COB = vehicle.calc_water_height()
    #     print(f"{vehicle.name} - Empty buoyancy engine, full hopper")
    #     print(f'Water height {water}, stability {COB - vehicle.COG}, net_force {vehicle.net_force} fully submerged, vehicle weight {vehicle.weight / 9.81}')
    output_data('output.csv', vehicles)


    #multiple_vehicles(vessels, heights, vehicle_data)
    #vehicle_comparisons(vessels, heights, vehicle_data)