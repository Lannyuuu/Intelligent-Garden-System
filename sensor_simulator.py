"""
Simulate two virtual sensors for an intelligent garden:
 1. Humidity sensor: random humidity value + drought alert if below threshold.
 2. Light sensor: simulate day-night cycle based on system clock.
Publishes JSON payload to MQTT topic "garden/data" every 2 seconds.
"""
import paho.mqtt.client as mqtt
import json
import random
import time
from datetime import datetime, timezone

# MQTT broker settings
BROKER = "localhost"
PORT = 1883
TOPIC = "garden/data"

# Threshold for drought alert (percent humidity)
DROUGHT_THRESHOLD = 30

# MQTT callbacks

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("Connected to MQTT broker, result code:", rc)
    else:
        print("Failed to connect, result code:", rc)

def simulate_humidity():
    """
    Generate a random humidity reading (0-100%).
    If below DROUGHT_THRESHOLD, add drought_alert = True.
    """
    humidity = random.uniform(20.0, 80.0)
    alert = humidity < DROUGHT_THRESHOLD
    return round(humidity, 1), alert


def simulate_light():
    """
    Simulate light level based on hour of day:
    - 06:00 to 18:00 -> high light (random 600-1000 lux)
    - otherwise -> low light (random 0-100 lux)
    """
    hour = datetime.now().hour
    if 6 <= hour < 18:
        light = random.uniform(600, 1000)
    else:
        light = random.uniform(0, 100)
    return round(light, 1)


def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.connect(BROKER, PORT, 60)
    client.loop_start()

    try:
        while True:
            timestamp = datetime.now(timezone.utc).isoformat()
            humidity, drought_alert = simulate_humidity()
            light = simulate_light()

            payload = {
                "timestamp": timestamp,
                "humidity": humidity,
                "drought_alert": drought_alert,
                "light": light
            }
            msg = json.dumps(payload)
            client.publish(TOPIC, msg, qos=1)
            print(f"Published: {msg}")
            time.sleep(2)

    except KeyboardInterrupt:
        print("Stopping sensor simulator...")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == '__main__':
    main()