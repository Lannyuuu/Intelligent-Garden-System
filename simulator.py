"""
Simulate three virtual sensors for an intelligent garden:
 1. Humidity sensor: random humidity value + drought alert if below threshold.
 2. Light sensor: simulate day-night cycle based on system clock.
 3. PHsensor: random PH value
 4. Rain sensor: random rain detection (10% probability)
 5. CO₂ sensor: simulate concentration fluctuations
Publishes JSON payload to MQTT topic "garden/sensors" every 2 seconds.
"""
import paho.mqtt.client as mqtt
import json
import random
import time
from datetime import datetime, timezone

# MQTT broker settings
BROKER = "localhost"
PORT = 1883
ENV_TOPIC = "garden/sensors" 

# Sensor thresholds
DROUGHT_THRESHOLD = 30
MIN_PH = 4.0
MAX_PH = 9.0

def on_connect(client, userdata, flags, rc, properties=None):
    print("Connected to MQTT broker" if rc == 0 else f"Connection failed with code {rc}")

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


def simulate_ph(current_ph=None):
    """
    Simulate soil pH fluctuations:
    - Initial value: random neutral pH between 5.0-8.0
    - Subsequent values: fluctuates ±0.3 from previous value
    - Constrained between MIN_PH and MAX_PH thresholds
    Returns value rounded to 1 decimal place
    """
    if current_ph is None:
        return round(random.uniform(4, 9), 1)
    change = random.uniform(-0.8, 0.8)
    return round(max(MIN_PH, min(MAX_PH, current_ph + change)), 1)


def simulate_rain():
    """Simulate rainfall detection (10% probability of rain)"""
    return random.random() < 0.1  # 10% chance of rain


def simulate_co2(current_co2=None):
    """
    Simulate CO₂ concentration levels:
    - Initial value: 400ppm (atmospheric standard)
    - Fluctuation range: ±50ppm
    - Recommended greenhouse optimization range: 800-1200ppm
    """
    if current_co2 is None:
        return random.uniform(350, 2000)  
    change = random.uniform(-200, 200)  
    return round(max(350, min(2000, current_co2 + change)), 1)



def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.connect(BROKER, PORT, 60)
    client.loop_start()

    try:
        current_ph = 6.5
        current_co2 = 400.0  
        
        while True:
            timestamp = datetime.now(timezone.utc).isoformat()
            
         
            humidity, drought_alert = simulate_humidity()
            light = simulate_light()
            current_ph = simulate_ph(current_ph)
            rain = simulate_rain()  
            current_co2 = simulate_co2(current_co2)  
            
         
            payload = {
              "timestamp": timestamp,
              "humidity": humidity,
              "drought_alert": drought_alert,
              "light": light,
              "ph": current_ph,
              "rain": rain,          
              "co2": current_co2   
}
            client.publish(ENV_TOPIC, json.dumps(payload), qos=1)
            
            print(f"Published combined data: {payload}")
            time.sleep(2)

    except KeyboardInterrupt:
        print("Stopping sensor simulator...")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == '__main__':
    main()