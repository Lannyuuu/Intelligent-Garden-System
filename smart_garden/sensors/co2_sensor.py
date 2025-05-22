"""CO2 sensor simulation module"""
import random
from .base_sensor import BaseSensor

class Co2Sensor(BaseSensor):
    """Simulates CO2 concentration sensor
    Simulate CO₂ concentration levels:
    - Initial value: 400ppm (atmospheric standard)
    - Fluctuation range: ±50ppm
    - Recommended greenhouse optimization range: 800-1200ppm
    """
    def __init__(self):
        super().__init__()
        self.current_co2 = 400.0  # Atmospheric baseline

    def read(self):
        """Generate CO2 value with fluctuation"""
        change = random.uniform(-200, 200)
        self.current_co2 = round(max(350, min(2000, self.current_co2 + change)), 1)
        return self.current_co2