---

layout: layouts/docs.njk
tags: docs
title: Hardware Setup
nav: Hardware Setup
navExclude: true
---

<div class="eyebrow">Getting Started</div>

# Hardware Setup

Connect the RH01T9k to the SPI controller using the pinout and requirements below.

## Tang Nano 9K pinout

<img class="pinout-image" src="/assets/images/RH01T9k-pinout.png" alt="RH01T9k Tang Nano 9K SPI and control pinout">

## Electrical requirements

* Use 3.3 V logic levels.
* Connect a common ground between the SPI controller and RH01T9k.

<div class="note"><strong>Caution:</strong> Do not connect incompatible I/O voltage levels directly to the emulator pins.</div>

## SPI requirements

* SCLK: up to 20 MHz
* SPI modes: 0, 1, 2, or 3
* Configure the controller and emulator for the same SPI mode.
* Keep CS low for the entire transaction and return it high between transactions.
* Transactions must contain a whole number of bytes.
* For Modes 1 and 3, provide a CS-to-SCLK setup delay before the first clock edge. One SCLK period is a conservative setting.

<div class="note"><strong>Note:</strong> A continuously asserted CS is treated as one continuous SPI transaction.</div>

## USB serial control

RH01T9k is configured from the computer through its USB serial connection.

The control baud rate is fixed at:

```text
115200 baud
```

Close any serial terminal or other program using the same port before running the Python API.

## Next step

Continue to [Quick Start](/quick-start/) to verify communication and configure the emulator from Python.
