"""Humidity sensor simulation module"""
import random
from .base_sensor import BaseSensor

class HumiditySensor(BaseSensor):
    """Simulates humidity sensor with drought detection"""
    def read(self, current_value=None):
        """Generate humidity value with drought alert"""
        if current_value is None:
            return self.generate_value(20.0, 90.0), False
            
        new_value = current_value + random.uniform(-5, 5)
        return round(max(0, min(100, new_value)), 1), new_value < 30