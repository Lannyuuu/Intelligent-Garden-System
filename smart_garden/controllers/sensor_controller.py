# File: controllers/sensor_controller.py (补全后)
"""Sensor data processing controller"""
import json
from typing import Dict, Any
from config import *
from .base_controller import BaseController

class SensorController(BaseController):
    """Handles sensor data processing and control commands"""
    def __init__(self, broker, port):
        super().__init__(broker, port)
        self.client.subscribe(SENSOR_TOPIC)
        self.client.on_message = self.on_message
        print(f"🔍 Subscribed to topic: {SENSOR_TOPIC}")

    def on_message(self, client, userdata, msg):
        """Process incoming sensor messages"""
        try:
            data = json.loads(msg.payload.decode())
            print(f"\n📊 Raw Sensor Data: {data}")
            
            # Rain check
            if data.get("rain"):
                self.handle_rain(data.get("rain"))
                
            # Individual sensor processing
            self.process_humidity(data.get("humidity"))
            self.process_light(data.get("light"))
            self.process_co2(data.get("co2"))
            self.process_ph(data.get("ph"))

        except Exception as e:
            print(f"❌ Data processing error: {e}")

    # Handlers for individual sensors
    def handle_rain(self, rain_status: bool):
        """Handle rain detection"""
        if rain_status:
            print("☔ Detected rain! Canceling irrigation...")
            self.publish_control({"action": "stop_watering"})

    def process_humidity(self, humidity: float):
        """Process humidity data"""
        if humidity < WATERING_THRESHOLD:
            self.trigger_watering(humidity)
        else:
            print(f"💧 Humidity OK: {humidity}% ≥ {WATERING_THRESHOLD}%")

    def trigger_watering(self, humidity: float):
        """Send watering command"""
        print(f"🚨 Low humidity! Current: {humidity}% (Threshold: {WATERING_THRESHOLD}%)")
        command = {"action": "water", "duration": 5}
        self.publish_control(command)
        print(f"💧 Sent watering command: {command}")

    def process_light(self, light: float):
        """Process light data"""
        if light < LIGHTING_THRESHOLD:
            self.trigger_light(light)
        else:
            print(f"💡 Light OK: {light}lux ≥ {LIGHTING_THRESHOLD}lux")

    def trigger_light(self, light: float):
        """Send lighting control command"""
        print(f"🌑 Low light! Current: {light}lux (Threshold: {LIGHTING_THRESHOLD}lux)")
        command = {"action": "light_on", "duration": 10}
        self.publish_control(command)
        print(f"💡 Sent light-on command: {command}")

    def process_co2(self, co2: float):
        """Process CO2 data"""
        if co2 < CO2_THRESHOLD_LOW:
            print(f"🌬️ Low CO₂! Current: {co2}ppm (Threshold: {CO2_THRESHOLD_LOW}ppm)")
            self.adjust_ventilation("enrich", 15)
        elif co2 > CO2_THRESHOLD_HIGH:
            print(f"⚠️ High CO₂! Current: {co2}ppm (Threshold: {CO2_THRESHOLD_HIGH}ppm)")
            self.adjust_ventilation("vent", 10)
        else:
            print(f"🌱 CO₂ Optimal: {co2}ppm")

    def adjust_ventilation(self, mode: str, duration: int):
        """Send ventilation control command"""
        command = {"action": "adjust_ventilation", "mode": mode, "duration": duration}
        self.publish_control(command)
        print(f"🌀 Sent ventilation command: {command}")

    def process_ph(self, ph: float):
        """Process pH data"""
        if ph < PH_THRESHOLD_LOW:
            print(f"🚨 Low PH! Current: {ph} (Threshold: {PH_THRESHOLD_LOW})")
            self.adjust_ph("alkaline", 10)
        elif ph > PH_THRESHOLD_HIGH:
            print(f"🚨 High PH! Current: {ph} (Threshold: {PH_THRESHOLD_HIGH})")
            self.adjust_ph("acidic", 10)
        else:
            print(f"🧪 PH normal: {ph}")

    def adjust_ph(self, substance: str, amount: int):
        """Send pH adjustment command"""
        command = {"action": "adjust_ph", "substance": substance, "amount": amount}
        self.publish_control(command)
        print(f"🧪 Sent PH adjustment command: {command}")

    def publish_control(self, command: Dict[str, Any]):
        """Publish control command to MQTT"""
        self.client.publish(CONTROL_TOPIC, json.dumps(command))