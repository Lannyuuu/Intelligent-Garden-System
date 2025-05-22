"""Rain sensor simulation module"""
import random
from .base_sensor import BaseSensor

class RainSensor(BaseSensor):
    """Simulates rain detection sensor (10% probability)"""
    def read(self):
        """Determine rain occurrence"""
        return random.random() < 0.1