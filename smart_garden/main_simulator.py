"""Main entry point for sensor simulator"""
import time
import json
from datetime import datetime, timezone
from config import MQTT_BROKER, MQTT_PORT, SENSOR_TOPIC
import paho.mqtt.client as mqtt
from sensors.humidity_sensor import HumiditySensor
from sensors.light_sensor import LightSensor
from sensors.ph_sensor import PhSensor
from sensors.co2_sensor import Co2Sensor
from sensors.rain_sensor import RainSensor

def create_sensor_simulator():
    """Create and return all sensor instances"""
    return {
        "humidity": HumiditySensor(),
        "light": LightSensor(),
        "ph": PhSensor(),
        "co2": Co2Sensor(),
        "rain": RainSensor()
    }

def main():
    client = mqtt.Client()
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    sensors = create_sensor_simulator()

    try:
        while True:
            payload = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "humidity": sensors["humidity"].read()[0],
                "drought_alert": sensors["humidity"].read()[1],
                "light": sensors["light"].read(),
                "ph": sensors["ph"].read(),
                "rain": sensors["rain"].read(),
                "co2": sensors["co2"].read()
            }
            
            client.publish(SENSOR_TOPIC, json.dumps(payload), qos=1)
            print(f"Published combined data: {payload}")
            time.sleep(2)

    except KeyboardInterrupt:
        print("Stopping sensor simulator...")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == '__main__':
    main()