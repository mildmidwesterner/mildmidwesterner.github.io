---
layout: layouts/docs.njk
tags: docs
title: BMI160 HIL Demo
nav: Demo
downloads:
  - name: 04_bmi160.py
    url: /assets/downloads/04_bmi160.py
  - name: ESP32_firmware.zip
    url: /assets/downloads/ESP32_firmware.zip
---

<div class="eyebrow">Demo</div>

# BMI160 Emulator Demo

<p class="lead">This demo replaces a BMI160 sensor with the RH01T9k using the same firmware intended for the  physical sensor.</p>

```text
Physical sensor test

ESP32  <---- SPI ---->  BMI160
  |
SSD1306 OLED
```

```text
Emulated sensor test

ESP32  <---- SPI ---->  RH01T9k
  |                          
SSD1306 OLED                 
                           
```

## Demo video

The demo begins with an ESP32 connected to BMI160. The ESP32 reads acceleration over SPI, and displays X/Y/Z values on an OLED. Moving the physical sensor changes the displayed values.

The BMI160 is then disconnected and replaced by the RH01T9k. The ESP32 continues sending the same SPI commands, but the RH01T9k now responds with simulated acceleration values controlled by Python. 

<video class="demo-video" controls preload="metadata">
  <source src="/assets/videos/bmi160_demo.mp4" type="video/mp4">
  Your browser does not support embedded video. Download the MP4 to watch the demo.
</video>

## How the emulation works

The ESP32 does not know whether the SPI peripheral is BMI160 sensor or the RH01T9k.

Python defines the BMI160 register values that the RH01T9k should expose. The emulated register map includes the chip ID, status and configuration registers, and the six acceleration bytes at addresses `0x12` through `0x17`.

The ESP32 initializes the device for a ±2 g range and 100 Hz accelerometer configuration, then repeatedly reads the acceleration registers and displays the result on the OLED.

Python updates the emulated acceleration registers with a synthetic tilt sequence: flat -> 45° tilt -> 90° tilt -> flat

The motion represents a tilt around the Y axis:

```text
X = sin(angle)
Y = 0
Z = -cos(angle)
```

Python converts the values to signed 16-bit accelerometer samples using 16,384 counts per g and updates them every 50 ms.

## Why this is useful for HIL testing

With a physical sensor, test inputs depend on physically moving or manipulating the device.

With the RH01T9k, the same firmware can be tested against controlled SPI responses generated from software. This makes sensor conditions repeatable and easier to automate.

For example, a test can provide:

- known acceleration values
- repeatable motion sequences
- boundary values
- unusual or invalid register states
- predefined inputs for regression testing
