---
layout: layouts/docs.njk
tags: docs
title: SPI Emulator for Firmware Testing
nav: Overview
permalink: /
description: Test firmware without a sensor using a programmable SPI slave emulator.
---

<div class="eyebrow">Overview</div>

# RH01T9k: SPI Emulator 

<p class="lead overview-intro">RH01T9k is a programmable SPI slave emulator built to test firmware over the physical SPI bus. A Python API configures RH01T9k over UART to control register values and SPI responses.</p>

<div class="overview-board-frame">
  <img class="overview-board-image" src="/assets/images/RH01T9k-overview.png" alt="RH01T9k board connected on a breadboard">
</div>

<p class="lead overview-after-image">This is not a software-mocked driver. It is an FPGA-based board (Tang Nano 9k) designed for embedded firmware testing, automated hardware testing, or HIL workflows.</p>


## Why emulate the peripheral? 

Firmware tests often need repeatable register values and specific SPI responses that are difficult to reproduce with a physical sensor. An SPI peripheral emulator makes those conditions programmable. 

Examples include returning an incorrect chip ID, feeding synthetic environmental sensor data to trigger firmware thresholds, and replaying repeatable peripheral states. 

## How the emulator works

The DUT/MCU is flashed with the same firmware it would use with the actual SPI sensor or peripheral. The target peripheral is replaced by the emulator on the SPI bus, while the firmware remains unchanged.

<div class="diagram">
  MCU ⇄ SPI ⇄ Emulator ⇄ UART ⇄ Python Script
</div>

The emulator is configured from Python to reproduce the behavior expected by the firmware. When the MCU issues SPI read or write transactions, the FPGA receives the MOSI traffic and returns the corresponding MISO data.

MOSI commands and MISO responses can also be captured by the emulator for debugging and automated test verification.

## Current features

- SPI modes 0, 1, 2, and 3 at up to 20 MHz
- Configurable read/write, and address command format
- A 256-byte programmable SPI register space
- Sequential and burst register access
- MOSI/MISO transaction for debugging

## Planned features

- Fault and error injection
- Command-map mode for custom protocols
- GPIO interrupt and sideband signal
