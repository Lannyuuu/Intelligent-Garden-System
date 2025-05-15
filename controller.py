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
SENSOR_TOPIC = "garden/sensors"
CONTROL_TOPIC = "garden/control"

# Control thresholds
WATERING_THRESHOLD = 30
LIGHTING_THRESHOLD = 500
PH_THRESHOLD_LOW = 6.0
PH_THRESHOLD_HIGH = 7.0
CO2_THRESHOLD_LOW = 800    
CO2_THRESHOLD_HIGH = 1500  
VENTILATION_THRESHOLD = 50 

def on_connect(client, userdata, flags, rc):
    print("✅ Connected to MQTT Broker!" if rc == 0 else f"❌ Connection failed with code {rc}")
    client.subscribe(SENSOR_TOPIC)
    print(f"🔍 Subscribed to topic: {SENSOR_TOPIC}")

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        humidity = data.get("humidity")
        light = data.get("light")
        ph = data.get("ph")
        timestamp = data.get("timestamp", "N/A")
        rain = data.get("rain")
        co2 = data.get("co2")
        
        # Print raw data (optional)
        print(f"\n📊 Raw Sensor Data: {data}")
        
        #raining check
        
        if rain is not None and rain:
            print("☔ Detected rain! Canceling irrigation...")
            client.publish(CONTROL_TOPIC, json.dumps({"action": "stop_watering"}))

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
        
         # CO2 check 
        if co2 is not None:
            if co2 < CO2_THRESHOLD_LOW:
                print(f"🌬️ Low CO₂! Current: {co2}ppm (Threshold: {CO2_THRESHOLD_LOW}ppm)")
                command = {
                    "action": "adjust_ventilation",
                    "mode": "enrich",
                    "duration": 15
                }
                client.publish(CONTROL_TOPIC, json.dumps(command))
                print(f"🌀 Sent ventilation command: {command}")
                
            elif co2 > CO2_THRESHOLD_HIGH:
                print(f"⚠️ High CO₂! Current: {co2}ppm (Threshold: {CO2_THRESHOLD_HIGH}ppm)")
                command = {
                    "action": "adjust_ventilation",
                    "mode": "vent",
                    "duration": 10
                }
                client.publish(CONTROL_TOPIC, json.dumps(command))
                print(f"🌀 Sent ventilation command: {command}")
                
            else:
                print(f"🌱 CO₂ Optimal: {co2}ppm")
 
        # PH check 
        if ph is not None:
            if ph < PH_THRESHOLD_LOW:
                print(f"🚨 Low PH! Current: {ph} (Threshold: {PH_THRESHOLD_LOW})")
                command = {
                    "action": "adjust_ph",
                    "substance": "alkaline",
                    "amount": 10
                }
                client.publish(CONTROL_TOPIC, json.dumps(command))
                print(f"🧪 Sent PH adjustment command: {command}")
                
            elif ph > PH_THRESHOLD_HIGH:
                print(f"🚨 High PH! Current: {ph} (Threshold: {PH_THRESHOLD_HIGH})")
                command = {
                    "action": "adjust_ph",
                    "substance": "acidic",
                    "amount": 10
                }
                client.publish(CONTROL_TOPIC, json.dumps(command))
                print(f"🧪 Sent PH adjustment command: {command}")
                
            else:
                print(f"🧪 PH normal: {ph}")

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