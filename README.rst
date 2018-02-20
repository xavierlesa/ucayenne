# ucayenne
A very light clone of Cayenne-MQTT-Python for MicroPython

Base on https://github.com/myDevicesIoT/Cayenne-MQTT-Python but internally 
implements `umqtt.simple` and `umqtt.robust`

## How to use

```python
from cayenne import CayenneMQTTClient

MQTT_USERNAME="your-uuid-username"
MQTT_PASSWORD="your-uuid-password"
MQTT_CLIENT_ID="your-uuid-device-id"

def on_message(message):
  print("message received: " + str(message))

client = CayenneMQTTClient()
client.on_message = on_message
client.begin(MQTT_USERNAME, MQTT_PASSWORD, MQTT_CLIENT_ID)

while True:
    client.client.check_msg()

client.celsiusWrite(1, 10.5)
```


