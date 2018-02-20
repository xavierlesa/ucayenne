"""
A very light clone of Cayenne-MQTT-Python for MicroPython

Base on https://github.com/myDevicesIoT/Cayenne-MQTT-Python

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
"""

from umqtt.robust import MQTTClient
from umqtt.simple import MQTTException
from . import __version__
import time

# Data types
TYPE_BAROMETRIC_PRESSURE = "bp" # Barometric pressure
TYPE_BATTERY = "batt" # Battery
TYPE_LUMINOSITY = "lum" # Luminosity
TYPE_PROXIMITY = "prox" # Proximity
TYPE_RELATIVE_HUMIDITY = "rel_hum" # Relative Humidity
TYPE_TEMPERATURE = "temp" # Temperature
TYPE_VOLTAGE = "voltage" # Voltage

# Unit types
UNIT_UNDEFINED = "null"
UNIT_PASCAL = "pa" # Pascal
UNIT_HECTOPASCAL = "hpa" # Hectopascal
UNIT_PERCENT = "p" # % (0 to 100)
UNIT_RATIO = "r" # Ratio
UNIT_VOLTS = "v" # Volts
UNIT_LUX = "lux" # Lux
UNIT_CENTIMETER = "cm" # Centimeter
UNIT_METER = "m" # Meter
UNIT_DIGITAL = "d" # Digital (0/1)
UNIT_FAHRENHEIT = "f" # Fahrenheit
UNIT_CELSIUS = "c" # Celsius
UNIT_KELVIN = "k" # Kelvin
UNIT_MILLIVOLTS = "mv" # Millivolts

# Topics
COMMAND_TOPIC = "cmd"
DATA_TOPIC = "data"
RESPONSE_TOPIC = "response"


# The callback for when a PUBLISH message is received from the server.
def on_message(client, cayenne, msg):
    if cayenne.on_message:
        message = CayenneMessage(msg)
        error = cayenne.on_message(message)
        if not error:
            # If there was no error, we send the new channel state, which should be the command value we received.
            cayenne.virtualWrite(message.channel, message.value)
        # Send a response showing we received the message, along with any error from processing it.
        cayenne.responseWrite(message.msg_id, error)
        
class CayenneMessage:
    """ This is a class that describes an incoming Cayenne message. It is
    passed to the on_message callback as the message parameter.

    Members:

    client_id : String. Client ID that the message was published on.
    topic : String. Topic that the message was published on.
    channel : Int. Channel that the message was published on.
    msg_id : String. The message ID.
    value : String. The message value.
    """
    def __init__(self, msg):
        topic_tokens = msg.topic.split('/')
        self.client_id = topic_tokens[3]
        self.topic = topic_tokens[4]
        self.channel = int(topic_tokens[5])
        # is an string?
        if isinstance(msg.payload, str):
            payload_tokens = msg.payload.split(',')
        # payload is a byte type, decode to string and split into ID and value
        else:
            payload_tokens = msg.payload.decode().split(',')
        self.msg_id = payload_tokens[0]
        self.value = payload_tokens[1]
        
    def __repr__(self):
        return str(self.__dict__)
        
class CayenneMQTTClient:
    """Cayenne MQTT Client class.
    
    This is the main client class for connecting to Cayenne and sending and receiving data.
    
    Standard usage:
    * Set on_message callback, if you are receiving data.
    * Connect to Cayenne using the begin() function.
    * Call loop() at intervals (or loop_forever() once) to perform message processing.
    * Send data to Cayenne using write functions: virtualWrite(), celsiusWrite(), etc.
    * Receive and process data from Cayenne in the on_message callback.

    The on_message callback can be used by creating a function and assigning it to CayenneMQTTClient.on_message member.
    The callback function should have the following signature: on_message(message)
    The message variable passed to the callback is an instance of the CayenneMessage class.
    """
    client = None
    rootTopic = ""
    connected = False
    reconnect = False
    on_message = None
    
    def begin(self, username, password, clientid, hostname='mqtt.mydevices.com', port=1883):
        """Initializes the client and connects to Cayenne.
        
        username is the Cayenne username.
        password is the Cayenne password.
        clientID is the Cayennne client ID for the device.
        hostname is the MQTT broker hostname.
        port is the MQTT broker port.
        """

        self.rootTopic = "v1/%s/things/%s" % (username, clientid)
        self.client = MQTTClient(clientid, hostname, port, username, password)

        cayenne = self
        def lambda_on_message(topic, payload):
            #print("lambda_on_message")
            topic = str(topic.decode())
            payload = str(payload.decode())
            #print(topic)
            #print(payload)
            
            # CayenneMessage expect a msg object with topic and payload attributes
            class Msg:
                def __init__(self, topic, payload):
                    self.topic = topic
                    self.payload = payload

            on_message(cayenne.client, cayenne, Msg(topic, payload))

        self.client.set_callback(lambda_on_message)

        try:
            self.client.connect(clean_session=True)
        except MQTTException(e):
            print("MQTTException %s\n" % str(e))
        else:
            self.connected = True
            command_topic = self.getCommandTopic()
            print("SUB %s\n" % command_topic)
            self.client.subscribe(command_topic)
            self.mqttPublish("%s/sys/model" % self.rootTopic, "micropython")
            self.mqttPublish("%s/sys/version" % self.rootTopic, __version__)

        print("Connecting to %s..." % hostname)


    
    def getDataTopic(self, channel):
        """Get the data topic string.
        
        channel is the channel to send data to.
        """
        return "%s/%s/%s" % (self.rootTopic, DATA_TOPIC, channel)
    
    def getCommandTopic(self):
        """Get the command topic string."""
        return "%s/%s/+" % (self.rootTopic, COMMAND_TOPIC)

    def getResponseTopic(self):
        """Get the response topic string."""
        return "%s/%s" % (self.rootTopic, RESPONSE_TOPIC)

    def virtualWrite(self, channel, value, dataType="", dataUnit=""):
        """Send data to Cayenne.
        
        channel is the Cayenne channel to use.
        value is the data value to send.
        dataType is the type of data.
        dataUnit is the unit of the data.
        """
        if (self.connected):
            topic = self.getDataTopic(channel)
            if dataType:
                payload = "%s,%s=%s" % (dataType, dataUnit, value)
            else:
                payload = value
            self.mqttPublish(topic, payload)

    def responseWrite(self, msg_id, error_message):
        """Send a command response to Cayenne.
        
        This should be sent when a command message has been received.
        msg_id is the ID of the message received.
        error_message is the error message to send. This should be set to None if there is no error.
        """
        if (self.connected):
            topic = self.getResponseTopic()
            if error_message:
                payload = "error,%s=%s" % (msg_id, error_message)
            else:
                payload = "ok,%s" % (msg_id)
            self.mqttPublish(topic, payload)            
            
    def celsiusWrite(self, channel, value):
        """Send a Celsius value to Cayenne.

        channel is the Cayenne channel to use.
        value is the data value to send.
        """
        self.virtualWrite(channel, value, TYPE_TEMPERATURE, UNIT_CELSIUS)

    def fahrenheitWrite(self, channel, value):
        """Send a Fahrenheit value to Cayenne.

        channel is the Cayenne channel to use.
        value is the data value to send.
        """
        self.virtualWrite(channel, value, TYPE_TEMPERATURE, UNIT_FAHRENHEIT)

    def kelvinWrite(self, channel, value):
        """Send a kelvin value to Cayenne.

        channel is the Cayenne channel to use.
        value is the data value to send.
        """
        self.virtualWrite(channel, value, TYPE_TEMPERATURE, UNIT_KELVIN)
    
    def luxWrite(self, channel, value):
        """Send a lux value to Cayenne.

        channel is the Cayenne channel to use.
        value is the data value to send.
        """
        self.virtualWrite(channel, value, TYPE_LUMINOSITY, UNIT_LUX)
    
    def pascalWrite(self, channel, value):
        """Send a pascal value to Cayenne.

        channel is the Cayenne channel to use.
        value is the data value to send.
        """
        self.virtualWrite(channel, value, TYPE_BAROMETRIC_PRESSURE, UNIT_PASCAL)
    
    def hectoPascalWrite(self, channel, value):
        """Send a hectopascal value to Cayenne.

        channel is the Cayenne channel to use.
        value is the data value to send.
        """
        self.virtualWrite(channel, value, TYPE_BAROMETRIC_PRESSURE, UNIT_HECTOPASCAL)

    def mqttPublish(self, topic, payload):
        """Publish a payload to a topic
        
        topic is the topic string.
        payload is the payload data.
        """
        print("PUB %s\n%s\n" % (topic, payload))
        self.client.publish(topic, payload, 0, False)    
