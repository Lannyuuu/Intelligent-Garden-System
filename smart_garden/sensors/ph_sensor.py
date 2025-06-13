"""PH sensor simulation module"""
import random
from .base_sensor import BaseSensor
from config import MIN_PH, MAX_PH

class PhSensor(BaseSensor):
    """Simulates soil pH sensor with safe range emphasis"""
    def __init__(self):
        super().__init__()
        # set initial value in the safe range
        self.current_ph = random.uniform(6.0, 7.0)
        # safe range
        self.safe_min = 6.0
        self.safe_max = 7.0
        # counts for beyond safe range
        self.outside_safe_count = 0
        # control the duration of exceeding the safe range
        self.outside_safe_duration = 0
        # directions beyond the safe range
        self.excursion_direction = None  # 'low' or 'high'

    def read(self):
        """Generate pH value with safe range emphasis"""
        # 20% chance that event will exceed the safe limit
        if not self.outside_safe_duration and random.random() < 0.2:
            # period begins to exceed the safelimit
            self.outside_safe_duration = random.randint(1, 5)  # continuously take 1-5 readings
            # determine the direction beyond(acidic or alkaline)
            if random.random() < 0.5:
                self.excursion_direction = 'low'
            else:
                self.excursion_direction = 'high'
        
        if self.outside_safe_duration > 0:
            # currently within the cycle that exceeds the safe limit
            self.outside_safe_duration -= 1
            
            # apply greater changes in the direction
            if self.excursion_direction == 'low':
                change = random.uniform(-0.4, -0.1)  # shift towards acidity
            else:  # 'high'
                change = random.uniform(0.1, 0.4)   # shift towards alkalinity
        else:
            # minor fluctuations within the safe range
            change = random.uniform(-0.2, 0.2)
            
            # if approaching the boundary, make sure not to accidentally go beyond by it
            if self.current_ph + change < self.safe_min:
                change = random.uniform(0.1, 0.2)  # only allow reduction
            elif self.current_ph + change > self.safe_max:
                change = random.uniform(-0.2, -0.1)  # only allow addition
        
        # apply chages and limit the scope
        new_ph = self.current_ph + change
        new_ph = max(MIN_PH, min(MAX_PH, new_ph))
        self.current_ph = round(new_ph, 1)
        
        return self.current_ph