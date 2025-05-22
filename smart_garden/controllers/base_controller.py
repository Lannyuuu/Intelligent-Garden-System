"""Base controller class for MQTT communication"""
import paho.mqtt.client as mqtt

class BaseController:
    """Base MQTT controller with connection handling"""
    def __init__(self, broker, port):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.connect(broker, port, 60)
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        print("✅ Connected to MQTT Broker!" if rc == 0 else f"❌ Connection failed with code {rc}")