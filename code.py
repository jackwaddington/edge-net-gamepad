"""edge-net-gamepad — read an Adafruit Mini I2C Gamepad (seesaw, 0x50),
publish button + joystick events to MQTT, and drive a local WS2812 strip
as optional feedback. See HARDWARE.md for the seesaw protocol.
"""

import time
import struct

import board
import busio

import wifi
import socketpool
import adafruit_minimqtt.adafruit_minimqtt as MQTT

import config

# ── Gamepad over I2C ────────────────────────────────────────────────────────
ADDR = 0x50

# seesaw pin -> short name used in MQTT topics
BUTTONS = {
    0:  "select",
    1:  "b",
    2:  "y",
    5:  "a",
    6:  "x",
    16: "start",
}
ALL = 0
for _pin in BUTTONS:
    ALL |= 1 << _pin

ADC_X, ADC_Y = 14, 15

i2c = busio.I2C(getattr(board, config.I2C_SCL), getattr(board, config.I2C_SDA))


def _write(base, reg, data=b""):
    while not i2c.try_lock():
        pass
    try:
        i2c.writeto(ADDR, bytes([base, reg]) + data)
    finally:
        i2c.unlock()
    time.sleep(0.001)


def _read(base, reg, n):
    while not i2c.try_lock():
        pass
    try:
        i2c.writeto(ADDR, bytes([base, reg]))
        time.sleep(0.001)
        buf = bytearray(n)
        i2c.readfrom_into(ADDR, buf)
    finally:
        i2c.unlock()
    return buf


def read_buttons():
    return ~struct.unpack(">I", _read(0x01, 0x04, 4))[0] & ALL


def read_adc(channel):
    return 1023 - struct.unpack(">H", _read(0x09, 0x07 + channel, 2))[0]


# init gamepad GPIO: inputs + pullups
_write(0x01, 0x03, struct.pack(">I", ALL))   # DIRCLR
_write(0x01, 0x0B, struct.pack(">I", ALL))   # PULLENSET

# ── Local LED strip (optional) ──────────────────────────────────────────────
pixels = None
if config.LED_PIN:
    import neopixel
    pixels = neopixel.NeoPixel(
        getattr(board, config.LED_PIN), config.NUM_LEDS, auto_write=True
    )
    pixels.brightness = 0.6
    pixels.fill((0, 0, 0))


def fill_strip(r, g, b):
    if pixels:
        pixels.fill((r, g, b))


# ── MQTT ────────────────────────────────────────────────────────────────────
def on_led(client, topic, message):
    if topic.endswith("/clear"):
        fill_strip(0, 0, 0)
        return
    try:
        r, g, b = (int(v) for v in message.split(","))
        fill_strip(r, g, b)
    except ValueError:
        pass


wifi.radio.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
pool = socketpool.SocketPool(wifi.radio)
mqtt = MQTT.MQTT(
    broker=config.MQTT_BROKER,
    port=config.MQTT_PORT,
    client_id=config.MQTT_CLIENT,
    socket_pool=pool,
    socket_timeout=1,
)
mqtt.on_message = on_led
mqtt.connect()
mqtt.subscribe("edge-net/gamepad/led")
mqtt.subscribe("edge-net/gamepad/led/clear")

# ── Main loop ───────────────────────────────────────────────────────────────
# This node mostly *publishes* input; it only *subscribes* for rare LED commands.
# mqtt.loop() blocks up to socket_timeout, so calling it every cycle would freeze
# input. Service incoming infrequently; publishing keeps the connection alive.
last_btns = 0
last_x = last_y = 512
CENTRE = 512
SERVICE_EVERY = 5          # seconds between mqtt.loop() calls for incoming
last_service = time.monotonic()

while True:
    now = time.monotonic()
    if now - last_service >= SERVICE_EVERY:
        mqtt.loop(timeout=1)
        last_service = now

    b = read_buttons()
    changed = b ^ last_btns
    for pin, name in BUTTONS.items():
        bit = 1 << pin
        if changed & bit:
            state = "press" if (b & bit) else "release"
            mqtt.publish("edge-net/gamepad/button/" + name, state)
            if state == "press" and pixels:
                fill_strip(40, 40, 40)   # quick local blip
    last_btns = b

    x = read_adc(ADC_X)
    y = read_adc(ADC_Y)
    if abs(x - CENTRE) > config.DEAD_ZONE and abs(x - last_x) > 8:
        mqtt.publish("edge-net/gamepad/axis/x", str(x))
        last_x = x
    if abs(y - CENTRE) > config.DEAD_ZONE and abs(y - last_y) > 8:
        mqtt.publish("edge-net/gamepad/axis/y", str(y))
        last_y = y

    time.sleep(0.02)
