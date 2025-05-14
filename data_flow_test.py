# data_flow_test.py
"""
Subscribe to garden/data topic and print incoming messages for testing data flow.
"""
import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Subscriber connected, subscribing to garden/data")
        client.subscribe("garden/data", qos=1)
    else:
        print("Subscriber failed to connect, rc=", rc)


def on_message(client, userdata, msg):
    print(f"Received on {msg.topic}: {msg.payload.decode()}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect("localhost", 1883, 60)

client.loop_forever()
