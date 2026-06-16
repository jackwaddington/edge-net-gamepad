# Edge-NET gamepad — host/network config. Edit, do not commit secrets.

WIFI_SSID     = "edge-net"
WIFI_PASSWORD = "CHANGE_ME"

MQTT_BROKER   = "192.168.50.1"   # the hub
MQTT_PORT     = 1883
MQTT_CLIENT   = "edge-net-gamepad"

# Host wiring
I2C_SCL = "GP5"
I2C_SDA = "GP4"
LED_PIN = "GP15"   # set to None to disable the local strip (pure input bridge)
NUM_LEDS = 50

# Joystick dead zone (counts either side of ~512 centre)
DEAD_ZONE = 80
