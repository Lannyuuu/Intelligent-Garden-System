import paho.mqtt.client as mqtt
import json
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from matplotlib.dates import DateFormatter
import matplotlib.animation as animation
from matplotlib.patches import Patch

# MQTT settings
BROKER = "localhost"
PORT = 1883
TOPIC = "garden/sensors"

# Data storage
max_data_points = 50
data_history = {
    'timestamp': [],
    'co2': [],
    'ph': [],
    'humidity': [],
    'light': []
}

# Threshold settings
THRESHOLDS = {
    'co2': {'low': 800, 'high': 1200},
    'ph': {'low': 6.0, 'high': 7.0},
    'humidity': {'low': 30, 'high': 80},
    'light': {'low': 500, 'high': 2000}
}

# Initialize figure
plt.figure(figsize=(14, 10))
plt.style.use('ggplot')


# MQTT callback
def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        timestamp = datetime.now()

        # Store data (keep only last max_data_points)
        data_history['timestamp'].append(timestamp)
        if len(data_history['timestamp']) > max_data_points:
            data_history['timestamp'].pop(0)

        if 'co2' in data:
            data_history['co2'].append(data['co2'])
            if len(data_history['co2']) > max_data_points:
                data_history['co2'].pop(0)

        if 'ph' in data:
            data_history['ph'].append(data['ph'])
            if len(data_history['ph']) > max_data_points:
                data_history['ph'].pop(0)

        if 'humidity' in data:
            data_history['humidity'].append(data['humidity'])
            if len(data_history['humidity']) > max_data_points:
                data_history['humidity'].pop(0)

        if 'light' in data:
            data_history['light'].append(data['light'])
            if len(data_history['light']) > max_data_points:
                data_history['light'].pop(0)

    except Exception as e:
        print(f"Error processing message: {e}")


# Animation update function
def update_plot(frame):
    plt.clf()

    if not data_history['timestamp']:
        return

    # Convert to numpy arrays for easier manipulation
    ts = np.array(data_history['timestamp'])

    # --- Plot 1: CO2 Levels ---
    plt.subplot(2, 2, 1)
    if data_history['co2']:
        plt.plot(ts, data_history['co2'], 'b-', linewidth=2, label='CO2 Level')

        # Add threshold lines
        plt.axhline(y=THRESHOLDS['co2']['low'], color='y', linestyle='--', label='Low Threshold')
        plt.axhline(y=THRESHOLDS['co2']['high'], color='r', linestyle='--', label='High Threshold')

        # Highlight abnormal values
        for i, val in enumerate(data_history['co2']):
            if val < THRESHOLDS['co2']['low']:
                plt.scatter(ts[i], val, color='yellow', s=100, zorder=5)
            elif val > THRESHOLDS['co2']['high']:
                plt.scatter(ts[i], val, color='red', s=100, zorder=5)

        plt.title('CO2 Concentration Monitoring')
        plt.ylabel('CO2 (ppm)')
        plt.ylim(500, 2000)
        plt.grid(True, alpha=0.3)
        plt.legend()

    # --- Plot 2: pH Levels ---
    plt.subplot(2, 2, 2)
    if data_history['ph']:
        plt.plot(ts, data_history['ph'], 'g-', linewidth=2, label='pH Level')

        # Add threshold lines
        plt.axhline(y=THRESHOLDS['ph']['low'], color='r', linestyle='--', label='Low Threshold')
        plt.axhline(y=THRESHOLDS['ph']['high'], color='y', linestyle='--', label='High Threshold')

        # Highlight abnormal values
        for i, val in enumerate(data_history['ph']):
            if val < THRESHOLDS['ph']['low']:
                plt.scatter(ts[i], val, color='red', s=100, zorder=5)
            elif val > THRESHOLDS['ph']['high']:
                plt.scatter(ts[i], val, color='yellow', s=100, zorder=5)

        plt.title('pH Level Monitoring')
        plt.ylabel('pH Value')
        plt.ylim(4, 10)
        plt.grid(True, alpha=0.3)
        plt.legend()

    # --- Plot 3: Humidity ---
    plt.subplot(2, 2, 3)
    if data_history['humidity']:
        plt.plot(ts, data_history['humidity'], 'm-', linewidth=2, label='Humidity')

        # Add threshold lines
        plt.axhline(y=THRESHOLDS['humidity']['low'], color='r', linestyle='--', label='Low Threshold')
        plt.axhline(y=THRESHOLDS['humidity']['high'], color='r', linestyle='--', label='High Threshold')

        plt.title('Humidity Monitoring')
        plt.ylabel('Humidity (%)')
        plt.ylim(0, 100)
        plt.grid(True, alpha=0.3)
        plt.legend()

    # --- Plot 4: Light Levels ---
    plt.subplot(2, 2, 4)
    if data_history['light']:
        plt.plot(ts, data_history['light'], color='orange', linewidth=2, label='Light Level')

        # Add threshold line
        plt.axhline(y=THRESHOLDS['light']['low'], color='r', linestyle='--', label='Low Threshold')

        plt.title('Light Level Monitoring')
        plt.ylabel('Light (lux)')
        plt.ylim(0, 3000)
        plt.grid(True, alpha=0.3)
        plt.legend()

    # Format x-axis
    date_form = DateFormatter("%H:%M:%S")
    for i in range(1, 5):
        plt.subplot(2, 2, i)
        plt.gca().xaxis.set_major_formatter(date_form)
        plt.gca().tick_params(axis='x', rotation=45)

    plt.tight_layout()


# Set up MQTT client
client = mqtt.Client()
client.on_message = on_message
client.connect(BROKER, PORT, 60)
client.subscribe(TOPIC)
client.loop_start()

# Set up animation
ani = animation.FuncAnimation(plt.gcf(), update_plot, interval=1000)

try:
    plt.show()
except KeyboardInterrupt:
    print("Stopping visualization...")
finally:
    client.loop_stop()
    client.disconnect()