"""Main entry point for sensor simulator with VAE environment generator"""
import time
import json
import sqlite3
from datetime import datetime, timezone
from config import MQTT_BROKER, MQTT_PORT, SENSOR_TOPIC, USE_VAE_GENERATOR
import paho.mqtt.client as mqtt

# select the import method based om the configuration
if USE_VAE_GENERATOR:
    from vae_generator.vae_sensor import VAESensorGenerator
    print(">>> Using VAE Environment Generator Mode <<<")
else:
    from sensors.humidity_sensor import HumiditySensor
    from sensors.light_sensor import LightSensor
    from sensors.ph_sensor import PhSensor
    from sensors.co2_sensor import Co2Sensor
    from sensors.rain_sensor import RainSensor
    print(">>> Using Real Sensor Simulation Mode <<<")

def format_float(value):
    # format the float number to retian one decimal
    return round(float(value), 1)

def insert_sensor_data(db_connection, timestamp, humidity, drought_alert, light, ph, rain, co2):
    #Insert sensor data into the database with proper type handling
    cursor = db_connection.cursor()
    cursor.execute('''
        INSERT INTO SensorData (Timestamp, Humidity, DroughtAlert, Light, PH, Rain, CO2)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        str(timestamp),          
        format_float(humidity),  
        int(bool(drought_alert)),
        format_float(light),     
        format_float(ph),        
        int(bool(rain)),        
        format_float(co2)        
    ))
    db_connection.commit()

def initialize_database(db_connection):
    #Ensure database table exists
    cursor = db_connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS SensorData (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Timestamp DATETIME NOT NULL,
            Humidity REAL NOT NULL,
            DroughtAlert INTEGER NOT NULL,
            Light REAL NOT NULL,
            PH REAL NOT NULL,
            Rain INTEGER NOT NULL,
            CO2 REAL NOT NULL
        )
    ''')
    db_connection.commit()

def create_sensor_simulator():
    #Create real sensor instances
    return {
        "humidity": HumiditySensor(),
        "light": LightSensor(),
        "ph": PhSensor(),
        "co2": Co2Sensor(),
        "rain": RainSensor()
    }

def load_initial_history(db_connection, seq_length):
    #Load initial history data for VAE generator
    cursor = db_connection.cursor()
    cursor.execute('''
        SELECT Humidity, DroughtAlert, Light, PH, Rain, CO2 
        FROM SensorData 
        ORDER BY Timestamp DESC 
        LIMIT ?
    ''', (seq_length,))
    
    history = cursor.fetchall()
    
    if len(history) < seq_length:
        print(f"Warning: Only {len(history)} records found, padding with zeros")
        
        padding = [(0.0, 0, 0.0, 7.0, 0, 400.0)] * (seq_length - len(history))
        history = padding + history
    
    return history

def create_safe_payload(payload):
    # create a secure JSON payload，ensure all the values are Python，and format the float numbers
    return {
        "timestamp": str(payload["timestamp"]),
        "humidity": format_float(payload["humidity"]),
        "drought_alert": bool(payload["drought_alert"]),
        "light": format_float(payload["light"]),
        "ph": format_float(payload["ph"]),
        "rain": bool(payload["rain"]),
        "co2": format_float(payload["co2"])
    }

def main():
    # connect to the database and initialized
    db_connection = sqlite3.connect('garden_sensor_data.db')
    initialize_database(db_connection)
    
    # set MQTT client
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    
    # according to config initialize sensor system
    if USE_VAE_GENERATOR:
        # create VAE environment generator
        generator = VAESensorGenerator()
        
        # from databse load history data to initialize the generator
        initial_history = load_initial_history(db_connection, generator.seq_length)
        generator.history = initial_history
        print(f"VAE Generator initialized with {len(initial_history)} historical records")
    else:
        # create real sensor simulator
        sensors = create_sensor_simulator()
        print("Real sensor simulator initialized")

    last_timestamp = None
    try:
        while True:
            # get timestamp（two models）
            current_time = datetime.now()
            timestamp = current_time.isoformat()
            
            # 检查是否与上次时间戳相同
            if last_timestamp and timestamp == last_timestamp:
                print("⚠️ 时间戳相同，等待下一秒...")
                time.sleep(1)
                continue
                
            # get sensor data（real or generate）
            if USE_VAE_GENERATOR:
                sensor_data = generator.generate()
                payload = {
                    "timestamp": timestamp,
                    "humidity": sensor_data["humidity"],
                    "drought_alert": sensor_data["drought_alert"],
                    "light": sensor_data["light"],
                    "ph": sensor_data["ph"],
                    "rain": sensor_data["rain"],
                    "co2": sensor_data["co2"]
                }
            else:
                humidity_value, drought_alert = sensors["humidity"].read()
                payload = {
                    "timestamp": timestamp,
                    "humidity": humidity_value,
                    "drought_alert": drought_alert,
                    "light": sensors["light"].read(),
                    "ph": sensors["ph"].read(),
                    "rain": sensors["rain"].read(),
                    "co2": sensors["co2"].read()
                }
            
            json_safe_payload = create_safe_payload(payload)
            
            # publish to MQTT
            client.publish(SENSOR_TOPIC, json.dumps(json_safe_payload), qos=1)
            print(f"Published data: {json.dumps(json_safe_payload, indent=2)}")
            
            # 更新上次时间戳
            last_timestamp = timestamp
            
            # insert the database
            insert_sensor_data(
                db_connection,
                json_safe_payload["timestamp"],
                json_safe_payload["humidity"],
                json_safe_payload["drought_alert"],
                json_safe_payload["light"],
                json_safe_payload["ph"],
                json_safe_payload["rain"],
                json_safe_payload["co2"]
            )
            
            # control frequency
            time.sleep(2)

    except KeyboardInterrupt:
        print("\nStopping sensor simulator...")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        # clean up resources
        client.loop_stop()
        client.disconnect()
        db_connection.close()
        print("Resources released. Goodbye!")

if __name__ == '__main__':
    main()