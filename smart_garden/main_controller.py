"""Main entry point for the garden controller"""
from config import MQTT_BROKER, MQTT_PORT
from controllers.sensor_controller import SensorController

if __name__ == "__main__":
    controller = SensorController(MQTT_BROKER, MQTT_PORT)
    print("🌱 Smart Garden Controller started...")
    # Keep main thread alive (MQTT loop runs in background)
    while True:
        pass