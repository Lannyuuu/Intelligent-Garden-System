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
TOPIC = "garden/data"

# Data storage
max_data_points = 30
timestamps = []
humidity_data = []
light_data = []
alert_status = []

# Initialize figure
plt.figure(figsize=(12, 8))
plt.style.use('ggplot')


# MQTT callback
def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())

        # Store data (keep only last max_data_points)
        timestamps.append(datetime.fromisoformat(data["timestamp"]))
        humidity_data.append(data["humidity"])
        light_data.append(data["light"])
        alert_status.append(data["drought_alert"])

        if len(timestamps) > max_data_points:
            timestamps.pop(0)
            humidity_data.pop(0)
            light_data.pop(0)
            alert_status.pop(0)

    except Exception as e:
        print(f"Error processing message: {e}")


# Animation update function
def update_plot(frame):
    plt.clf()

    if not timestamps:
        return

    # Convert to numpy arrays for easier manipulation
    ts = np.array(timestamps)
    hum = np.array(humidity_data)
    light = np.array(light_data)
    alerts = np.array(alert_status)

    # --- Plot 1: Humidity with drought alerts ---
    plt.subplot(2, 1, 1)

    # Plot humidity data
    line, = plt.plot(ts, hum, 'b-', linewidth=2, label='Humidity')

    # Add drought threshold line
    plt.axhline(y=30, color='r', linestyle='--', label='Drought Threshold')

    # Highlight drought periods
    alert_indices = np.where(alerts)[0]
    for i in alert_indices:
        if i < len(ts) - 1:
            plt.axvspan(ts[i], ts[i + 1], color='red', alpha=0.3)

    plt.title('Garden Humidity Monitoring (Drought Alert when <30%)')
    plt.ylabel('Humidity (%)')
    plt.ylim(0, 100)
    plt.grid(True, alpha=0.3)

    # Add custom legend
    legend_elements = [
        Patch(facecolor='red', alpha=0.3, label='Drought Alert'),
        Patch(facecolor='none', edgecolor='r', linestyle='--', label='Threshold')
    ]
    plt.legend(handles=legend_elements, loc='upper right')

    # --- Plot 2: Light Levels with Day/Night indication ---
    plt.subplot(2, 1, 2)

    # Plot light data
    plt.plot(ts, light, color='orange', linewidth=2, label='Light Level')

    # Add day/night background
    for i in range(len(ts) - 1):
        hour = ts[i].hour
        if 6 <= hour < 18:  # Daytime
            plt.axvspan(ts[i], ts[i + 1], color='yellow', alpha=0.1)
        else:  # Nighttime
            plt.axvspan(ts[i], ts[i + 1], color='blue', alpha=0.1)

    plt.title('Light Level Monitoring (Day/Night Cycle)')
    plt.ylabel('Light (lux)')
    plt.ylim(-50, 1100)  # Slightly below 0 to see markers clearly
    plt.grid(True, alpha=0.3)

    # Add custom legend
    legend_elements = [
        Patch(facecolor='yellow', alpha=0.1, label='Daytime (6:00-18:00)'),
        Patch(facecolor='blue', alpha=0.1, label='Nighttime')
    ]
    plt.legend(handles=legend_elements, loc='upper right')

    # Format x-axis
    date_form = DateFormatter("%H:%M:%S")
    for i in [1, 2]:
        plt.subplot(2, 1, i)
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