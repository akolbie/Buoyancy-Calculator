from cmath import sqrt
from tkinter.tix import Tree


WATER_DENSITY = 1000 #kg/m^3
DEPTH = 30 #m
SURFACE_NEUTRAL = 8.75 #L
CD = 1
AREA = 0.63 #m^3

class Vehicle():
    def __init__(self, pump_flow_rate):
        self.height = 0
        self.total_buoy_vessel_volume = 30
        self.nodule_weight = 12.5
        self.surface_neutral = (self.total_buoy_vessel_volume - self.nodule_weight) / 2
        self.buoy_volume = 0
        self.pump_flow_rate = pump_flow_rate
        self.time_step = 1 #s
        self.output = []

    def net_force(self):
        return (self.surface_neutral - self.buoy_volume) * 9.81

    def terminal_velocity(self):
        return self.net_force() / abs(self.net_force()) * sqrt(abs(self.net_force()) / (0.5 * WATER_DENSITY * CD * AREA))
        
    def height_delta(self):
        return self.terminal_velocity() * self.time_step

    def run_simulation(self):
        while True:



if __name__ == "__main__":
    while True:
