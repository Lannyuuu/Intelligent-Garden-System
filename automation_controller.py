import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime
from paho.mqtt.client import CallbackAPIVersion

# MQTT broker configuration
BROKER = "localhost"
PORT = 1883

# MQTT topics for communication
SENSOR_TOPIC = "garden/data"                  # Topic for receiving sensor data
WATER_PUMP_TOPIC = "garden/control/water_pump" # Topic for controlling water pump
LED_LIGHT_TOPIC = "garden/control/led_light"   # Topic for controlling LED lights
STATUS_TOPIC = "garden/status"                 # Topic for system status updates

# Threshold values for automatic control
DROUGHT_THRESHOLD = 30   # Soil humidity percentage below which watering is triggered
LIGHT_THRESHOLD = 500    # Light intensity in lux below which LED lights are turned on

# Duration for which controls remain active (in seconds)
WATERING_DURATION = 2    # Changed to 2 seconds to match update frequency
LIGHTING_DURATION = 2    # Changed to 2 seconds to match update frequency

class GardenController:
    def __init__(self):
        """Initialize the MQTT client and set up callbacks"""
        self.client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
        # Control state variables
        self.water_pump_on = False
        self.led_light_on = False
        self.last_update = 0
        self.update_interval = 2  # Process updates every 2 seconds
        
        # Connect to broker and start network loop
        self.client.connect(BROKER, PORT, 60)
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc, properties=None):
        """Callback for when the client connects to the broker"""
        if rc == 0:
            self.log("Controller connected to MQTT broker")
            self.client.subscribe(SENSOR_TOPIC)  # Subscribe to sensor data topic
        else:
            self.log(f"Connection failed with code {rc}", "ERROR")

    def on_message(self, client, userdata, msg):
        """Callback for when a message is received from the broker"""
        try:
            current_time = time.time()
            # Ensure updates are processed only at the specified interval
            if current_time - self.last_update >= self.update_interval:
                self.last_update = current_time
                data = json.loads(msg.payload.decode())
                self.log(f"Received sensor data: {data}")
                
                # Control logic based on sensor readings
                if data.get("humidity") < DROUGHT_THRESHOLD and not self.water_pump_on:
                    self.activate_water_pump()
                if data.get("light") < LIGHT_THRESHOLD and not self.led_light_on:
                    self.activate_led_light()
        except Exception as e:
            self.log(f"Error processing message: {str(e)}", "ERROR")

    def activate_water_pump(self):
        """Turn on water pump for the specified duration"""
        self.water_pump_on = True
        self.client.publish(WATER_PUMP_TOPIC, "ON")
        self.log("Water pump activated")
        
        # Non-blocking wait (keeps MQTT loop running)
        end_time = time.time() + WATERING_DURATION
        while time.time() < end_time:
            time.sleep(0.1)  # Short sleep to avoid blocking
            
        self.client.publish(WATER_PUMP_TOPIC, "OFF")
        self.water_pump_on = False
        self.log("Water pump deactivated")

    def activate_led_light(self):
        """Turn on LED lights for the specified duration"""
        self.led_light_on = True
        self.client.publish(LED_LIGHT_TOPIC, "ON")
        self.log("LED light activated")
        
        # Non-blocking wait
        end_time = time.time() + LIGHTING_DURATION
        while time.time() < end_time:
            time.sleep(0.1)
            
        self.client.publish(LED_LIGHT_TOPIC, "OFF")
        self.led_light_on = False
        self.log("LED light deactivated")

    def log(self, message, level="INFO"):
        """Create structured log entries with timestamps"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message
        }
        print(json.dumps(log_entry, indent=2))

if __name__ == "__main__":
    # Create and run the controller
    controller = GardenController()
    try:
        while True:
            time.sleep(0.1)  # Small sleep to reduce CPU usage
    except KeyboardInterrupt:
        print("Controller stopped")