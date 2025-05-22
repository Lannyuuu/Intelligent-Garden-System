from flask import Flask, render_template
import paho.mqtt.client as mqtt
import json
from datetime import datetime

app = Flask(__name__)

# ========== MQTT Configuration ==========
BROKER = "localhost"
PORT = 1883
TOPIC = "garden/sensors"  # Must match your publisher

# ========== Sensor Data Storage ==========
sensor_data = {
    "timestamp": "Waiting for data...",
    "humidity": 0,
    "drought_alert": False,
    "light": 0,
    "ph": 0,
    "rain": False,
    "co2": 0,
    "last_update": "Never updated"
}


# ========== MQTT Callbacks ==========
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("✅ Successfully connected to MQTT broker!")
        client.subscribe(TOPIC)
    else:
        print(f"❌ Connection failed with code: {rc}")


def on_message(client, userdata, msg):
    global sensor_data
    try:
        data = json.loads(msg.payload.decode())

        # Convert timestamp to local time
        utc_time = datetime.fromisoformat(data["timestamp"])
        local_time = utc_time.astimezone().strftime("%Y-%m-%d %H:%M:%S")

        # Update all sensor data
        sensor_data.update({
            "timestamp": local_time,
            "humidity": data["humidity"],
            "drought_alert": data["drought_alert"],
            "light": data["light"],
            "ph": data["ph"],
            "rain": data["rain"],
            "co2": data["co2"],
            "last_update": datetime.now().strftime("%H:%M:%S")
        })

        print(f"Data received: {sensor_data}")

    except Exception as e:
        print(f"❌ Data processing error: {e}")


# ========== MQTT Client Setup ==========
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

try:
    mqtt_client.connect(BROKER, PORT, 60)
    mqtt_client.loop_start()
except Exception as e:
    print(f"⚠️ MQTT connection error: {e}")


# ========== Flask Routes ==========
@app.route('/')
def index():
    return render_template('index.html', data=sensor_data)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)