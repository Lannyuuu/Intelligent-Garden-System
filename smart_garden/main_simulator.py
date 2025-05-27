"""Main entry point for sensor simulator"""
import time
import json
import sqlite3
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
    
def insert_sensor_data(db_connection, timestamp, humidity, drought_alert, light, ph, rain, co2):
    """Insert sensor data into the database"""
    cursor = db_connection.cursor()
    cursor.execute('''
        INSERT INTO SensorData (Timestamp, Humidity, DroughtAlert, Light, PH, Rain, CO2)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (timestamp, humidity, drought_alert, light, ph, rain, co2))
    db_connection.commit()


def main():
    # Connect to SQLite database
    db_connection = sqlite3.connect('garden_sensor_data.db')
    client = mqtt.Client()
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    sensors = create_sensor_simulator()

    try:
        while True:
            humidity_value, drought_alert = sensors["humidity"].read()
            payload = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "humidity": humidity_value,
                "drought_alert": drought_alert,
                "light": sensors["light"].read(),
                "ph": sensors["ph"].read(),
                "rain": sensors["rain"].read(),
                "co2": sensors["co2"].read()
            }
            
            client.publish(SENSOR_TOPIC, json.dumps(payload), qos=1)
            print(f"Published combined data: {payload}")
            
            drought_alert_int = 1 if payload["drought_alert"] else 0
            rain_int = 1 if payload["rain"] else 0
             # Insert data into SQLite database
            insert_sensor_data(
                db_connection,
                payload["timestamp"],
                payload["humidity"],
                drought_alert_int,
                payload["light"],
                payload["ph"],
                rain_int,
                payload["co2"]
            )
            
            time.sleep(2)

    except KeyboardInterrupt:
        print("Stopping sensor simulator...")
    finally:
        client.loop_stop()
        client.disconnect()
        db_connection.close()

if __name__ == '__main__':
    main()