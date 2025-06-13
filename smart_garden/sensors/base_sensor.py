"""Base class for sensor simulations"""
import random
from datetime import datetime, timezone

class BaseSensor:
    """Base class for all sensor simulations"""
    def __init__(self):
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def generate_value(self, min_val, max_val):
        """Generate random value within range"""
        return round(random.uniform(min_val, max_val), 1)