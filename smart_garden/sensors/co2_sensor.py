"""CO2 sensor simulation module"""
import random
from .base_sensor import BaseSensor

class Co2Sensor(BaseSensor):
    """Simulates CO2 concentration sensor with realistic fluctuations
    Simulate CO₂ concentration levels:
    - Most readings (80%) in optimal range (800-1200ppm)
    - Occasional excursions (20%) outside this range
    - Global limits: 350-2000ppm
    """
    def __init__(self):
        super().__init__()
        self.current_co2 = 1000.0  # Start in optimal range
        self.in_excursion = False  # Track if currently in excursion state
        self.excursion_duration = 0  # Duration of current excursion
        self.excursion_direction = None  # 'high' or 'low'

    def read(self):
        """Generate CO2 value with realistic fluctuations"""
        # 80% chance of normal operation in optimal range
        if not self.in_excursion and random.random() < 0.8:
            # Normal fluctuation within optimal range
            change = random.uniform(-50, 50)
            new_value = self.current_co2 + change
            
            # Keep within optimal range
            if new_value < 800:
                new_value = 800 + random.uniform(0, 20)  # Bounce off lower bound
            elif new_value > 1200:
                new_value = 1200 - random.uniform(0, 20)  # Bounce off upper bound
                
        else:
            # 20% chance of excursion outside optimal range
            if not self.in_excursion:
                # Start new excursion
                self.in_excursion = True
                self.excursion_duration = random.randint(1, 5)  # Last 1-5 readings
                self.excursion_direction = random.choice(['high', 'low'])
            
            # Apply excursion changes
            if self.excursion_direction == 'high':
                change = random.uniform(30, 100)  # Rising trend
            else:  # 'low'
                change = random.uniform(-100, -30)  # Falling trend
                
            new_value = self.current_co2 + change
            
            # Decrement excursion duration
            self.excursion_duration -= 1
            if self.excursion_duration <= 0:
                self.in_excursion = False
                
                # Start returning toward optimal range
                if new_value > 1200:
                    new_value -= random.uniform(50, 100)
                elif new_value < 800:
                    new_value += random.uniform(50, 100)
        
        # Apply global limits
        self.current_co2 = round(max(350, min(2000, new_value)), 1)
        return self.current_co2