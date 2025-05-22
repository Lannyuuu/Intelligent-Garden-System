"""Light sensor simulation module"""
from .base_sensor import BaseSensor
from datetime import datetime

class LightSensor(BaseSensor):
    """Simulates light sensor with day/night cycle

    Simulate light level based on hour of day:
    - 06:00 to 18:00 -> high light (random 600-1000 lux)
    - otherwise -> low light (random 0-100 lux)
    """
    def read(self):
        """Generate light value based on time of day"""
        hour = datetime.now().hour
        if 6 <= hour < 18:
            return self.generate_value(600, 1000)
        return self.generate_value(0, 100)