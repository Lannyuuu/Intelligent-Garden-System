"""PH sensor simulation module"""
import random
from .base_sensor import BaseSensor
from config import MIN_PH, MAX_PH

class PhSensor(BaseSensor):
    """Simulates soil pH sensor with gradual changes"""
    def __init__(self):
        super().__init__()
        self.current_ph = 6.5  # Initial neutral value

    def read(self):
        """Generate pH value with gradual fluctuation
         Simulate soil pH fluctuations:
         - Initial value: random neutral pH between 4.0-9.0
         - Subsequent values: fluctuates ±0.3 from previous value
         - Constrained between MIN_PH and MAX_PH thresholds
         Returns value rounded to 1 decimal place"""
        change = random.uniform(-0.6, 0.6)
        self.current_ph = round(max(MIN_PH, min(MAX_PH, self.current_ph + change)), 1)
        return self.current_ph