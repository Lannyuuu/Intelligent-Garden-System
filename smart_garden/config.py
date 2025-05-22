"""Project configuration constants"""

# MQTT Configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
SENSOR_TOPIC = "garden/sensors"
CONTROL_TOPIC = "garden/control"

# Control Thresholds
WATERING_THRESHOLD = 30
LIGHTING_THRESHOLD = 500
PH_THRESHOLD_LOW = 6.0
PH_THRESHOLD_HIGH = 7.0
CO2_THRESHOLD_LOW = 800    
CO2_THRESHOLD_HIGH = 1500  
VENTILATION_THRESHOLD = 50
DROUGHT_THRESHOLD = 30
MIN_PH = 4.0
MAX_PH = 9.0