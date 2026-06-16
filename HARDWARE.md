# Hardware

The portable spec. Everything here is a property of the gamepad itself, not the host board — it holds whether the gamepad is plugged into a Plasma Stick, a Pico W, or a Pi.

## Physical assembly

The [Adafruit Mini I2C Gamepad](https://www.adafruit.com/product/5743) plugs into the host's STEMMA QT / Qwiic port with a single 4-pin JST-SH cable — SDA, SCL, 3.3V, GND. No soldering. STEMMA QT daisy-chains, so other I2C devices (a sensor, a display) can share the bus.

On the Plasma Stick 2040W:

```
Plasma Stick 2040W (RP2040 + WiFi)
│
├── GP4  (SDA) ──┐
├── GP5  (SCL) ──┤ STEMMA QT ──── Gamepad (seesaw, addr 0x50)
├── 3.3V      ──┤
├── GND       ──┘
│
└── GP15 ──────── WS2812 LED strip (50 LEDs)
```

## Seesaw

The gamepad is an Adafruit seesaw chip at I2C address `0x50`. Buttons hang off seesaw GPIO; the joystick off seesaw ADC. No Pi/Pico GPIO is used by the gamepad — it is all over I2C.

### Buttons (seesaw GPIO)

| Adafruit label | Seesaw pin | Physical position |
|----------------|-----------|-------------------|
| Select | 0 | small left button |
| B | 1 | bottom face button |
| Y | 2 | left face button |
| A | 5 | right face button |
| X | 6 | top face button |
| Start | 16 | small right button |

Buttons read LOW when pressed. Read all at once via a seesaw GPIO bulk read, then invert so pressed = 1.

Pin mask:

```
ALL = (1<<0 | 1<<1 | 1<<2 | 1<<5 | 1<<6 | 1<<16)
```

### Joystick (seesaw ADC)

| Axis | ADC channel | Seesaw register |
|------|-------------|-----------------|
| X (left/right) | 14 | `0x09, 0x07+14 = 0x15` |
| Y (up/down) | 15 | `0x09, 0x07+15 = 0x16` |

Values 0–1023. Invert both: `x = 1023 - read_adc(14)`, `y = 1023 - read_adc(15)`. Centre at rest is ~512. Use a dead zone of ~80 counts either side so a resting stick is silent on the network.

## Raw seesaw I2C protocol (no library)

```python
# Write
i2c.writeto(ADDR, bytes([module, function]) + data)

# Read
i2c.writeto(ADDR, bytes([module, function]))
time.sleep(0.001)
i2c.readfrom_into(ADDR, buf)

# GPIO init (set inputs + pullups)
_write(0x01, 0x03, struct.pack('>I', pin_mask))   # DIRCLR
_write(0x01, 0x0B, struct.pack('>I', pin_mask))   # PULLENSET

# GPIO read (all buttons at once)
raw = struct.unpack('>I', _read(0x01, 0x04, 4))[0]
pressed = ~raw & pin_mask   # invert: pressed = 1

# ADC read (one axis)
val = struct.unpack('>H', _read(0x09, 0x07 + channel, 2))[0]
```

## Moving to another host

Only two things are host-specific:

1. **I2C pins** — change `busio.I2C(SCL, SDA)` to the host's pins. The gamepad address (`0x50`) and all seesaw registers are unchanged.
2. **WiFi / NeoPixel pin** — set in [config.py](config.py). The local LED strip is optional; drop it and the node becomes a pure MQTT input bridge.

The button map, ADC channels, and MQTT topic schema do not change. That is the whole reason this is its own repo.
