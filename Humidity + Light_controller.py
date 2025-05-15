"""
garden_controller.py (Enhanced)
- Subscribes to sensor data and prints real-time values
- Prints detailed thresholds comparisons when values are insufficient
- Triggers control commands when needed
"""

import paho.mqtt.client as mqtt
import json

# MQTT Configuration
BROKER = "localhost"
PORT = 1883
SENSOR_TOPIC = "garden/data"
CONTROL_TOPIC = "garden/control"

# Control thresholds
WATERING_THRESHOLD = 30    # Humidity threshold (%)
LIGHTING_THRESHOLD = 500   # Light intensity threshold (lux)

def on_connect(client, userdata, flags, rc):
    print("✅ Connected to MQTT Broker!" if rc == 0 else f"❌ Connection failed with code {rc}")
    client.subscribe(SENSOR_TOPIC)
    print(f"🔍 Subscribed to topic: {SENSOR_TOPIC}")

def on_message(client, userdata, msg):
    """Process sensor data and print detailed status"""
    try:
        data = json.loads(msg.payload.decode())
        humidity = data.get("humidity")
        light = data.get("light")
        timestamp = data.get("timestamp", "N/A")

        # Print raw data (optional)
        print(f"\n📊 Raw Sensor Data: {data}")

        # Humidity check
        if humidity is not None:
            if humidity < WATERING_THRESHOLD:
                print(f"🚨 Low humidity! Current: {humidity}% (Threshold: {WATERING_THRESHOLD}%)")
                command = {"action": "water", "duration": 5}
                client.publish(CONTROL_TOPIC, json.dumps(command))
                print(f"💧 Sent watering command: {command}")
            else:
                print(f"💧 Humidity OK: {humidity}% ≥ {WATERING_THRESHOLD}%")

        # Light check
        if light is not None:
            if light < LIGHTING_THRESHOLD:
                print(f"🌑 Low light! Current: {light}lux (Threshold: {LIGHTING_THRESHOLD}lux)")
                command = {"action": "light_on", "duration": 10}
                client.publish(CONTROL_TOPIC, json.dumps(command))
                print(f"💡 Sent light-on command: {command}")
            else:
                print(f"💡 Light OK: {light}lux ≥ {LIGHTING_THRESHOLD}lux")

        print(f"⏰ Data timestamp: {timestamp}")

    except Exception as e:
        print(f"❌ Data processing error: {e}")

def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, 60)
    print("🌱 Smart Garden Controller started...")
    client.loop_forever()

if __name__ == "__main__":
    main()
