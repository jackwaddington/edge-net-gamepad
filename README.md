# edge-net-gamepad

A node in [Edge-NET](https://github.com/jackwaddington/edge-net). An [Adafruit Mini I2C Gamepad](https://www.adafruit.com/product/5743) (STEMMA QT, seesaw) turned into a **network input device** — 6 buttons and an analog joystick that publish to MQTT. Whatever is on the bus can react: LED strip, GFX display, relays, Kindle.

The gamepad is the richest input surface on Edge-NET — analog stick plus six buttons, more than the Keybow's three buttons or the GFX Pack's five. It is the natural *universal remote* for the network.

## What this repo is

The gamepad is one self-contained piece, documented here so it can move between host boards. It is **just an I2C device** — it needs a host with a STEMMA QT / Qwiic port (or any I2C pins) and WiFi to publish.

Current host: **[Pimoroni Plasma Stick 2040W](https://shop.pimoroni.com/products/plasma-stick-2040-w)** (Pico W / RP2040 + WiFi, CircuitPython). The Plasma Stick runs a **dual role**:

1. Reads the gamepad and **publishes** button/joystick events to MQTT.
2. Drives its own **50-LED WS2812 strip** as local visual feedback.

Move the gamepad to a Pico W, a Pi, or any I2C+WiFi board and only [config.py](config.py) and the host wiring change — the protocol and topic schema in [HARDWARE.md](HARDWARE.md) stay identical.

## Hardware

| Part | Notes |
|------|-------|
| [Adafruit Mini I2C Gamepad with seesaw](https://www.adafruit.com/product/5743) | Product #5743, I2C addr `0x50` |
| [Pimoroni Plasma Stick 2040W](https://shop.pimoroni.com/products/plasma-stick-2040-w) | Host board — RP2040 + WiFi, CircuitPython |
| WS2812 / NeoPixel strip | 50 LEDs on `GP15` (local feedback) |

Gamepad plugs straight into the Plasma Stick's STEMMA QT port (SDA=`GP4`, SCL=`GP5`, 3.3V, GND). Wiring and the raw seesaw protocol: [HARDWARE.md](HARDWARE.md).

## IO

**Inputs** (read from gamepad over I2C):

| Control | Seesaw | Notes |
|---------|--------|-------|
| Buttons: Select, B, Y, A, X, Start | GPIO 0, 1, 2, 5, 6, 16 | LOW = pressed |
| Joystick X / Y | ADC ch 14 / 15 | 0–1023, centre ~512, dead zone ~80 |

**Outputs**:

| Output | Where | Notes |
|--------|-------|-------|
| 50× WS2812 LED | host board `GP15` | local feedback, also remote-controllable via MQTT |

## MQTT topics

**Publishes** — input events:

| Topic | Payload | When |
| ----- | ------- | ---- |
| `edge-net/gamepad/button/<name>` | `press` / `release` | button edge — `<name>` ∈ a, b, x, y, start, select |
| `edge-net/gamepad/axis/x` | `0`–`1023` | joystick X moves past dead zone (throttled) |
| `edge-net/gamepad/axis/y` | `0`–`1023` | joystick Y moves past dead zone (throttled) |

**Subscribes** — remote control of the local strip (optional, matches the [plasma](https://github.com/jackwaddington/edge-net-plasma) pattern):

| Topic | Payload | Effect |
| ----- | ------- | ------ |
| `edge-net/gamepad/led` | `r,g,b` | fill the whole strip |
| `edge-net/gamepad/led/clear` | — | turn strip off |

This decoupling is the point: the gamepad no longer hardcodes "joystick → my own hue". It publishes intent; any node decides what to do with it. The local strip is just one subscriber that happens to live on the same board.

## What it can drive

| Target | Example |
|--------|---------|
| [plasma](https://github.com/jackwaddington/edge-net-plasma) LEDs | joystick → hue, buttons → pattern |
| [gfx](https://github.com/jackwaddington/edge-net-gfx) display | joystick → menu nav, A → select, Start → home |
| [keybow](https://github.com/jackwaddington/edge-net-keybow) LEDs | light a button from the gamepad |
| [automation](https://github.com/jackwaddington/edge-net-automation) relay | button → switch power |
| [kindle](https://github.com/jackwaddington/edge-net-kindle) | navigate display modes |

## Software

CircuitPython. Copy onto the host's `CIRCUITPY` drive:

```bash
cp code.py config.py /Volumes/CIRCUITPY/
```

Set WiFi + broker in [config.py](config.py) first. Serial console:

```bash
screen /dev/tty.usbmodem* 115200
```

Requires the `adafruit_minimqtt` library in `CIRCUITPY/lib/` (from the CircuitPython library bundle).

## Part of Edge-NET

See [Edge-NET](https://github.com/jackwaddington/edge-net) for the full architecture and list of nodes.
