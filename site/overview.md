---
layout: layouts/docs.njk
tags: docs
title: SPI Peripheral Emulator for Firmware Testing
nav: Overview
permalink: /
description: Programmable SPI peripheral emulator for testing embedded firmware with repeatable register responses, hardware-in-the-loop testing, and automation.
---

<div class="eyebrow">Overview</div>

# RH01T9k: SPI Peripheral Emulator

<p class="lead overview-intro">
RH01T9k is a programmable SPI peripheral emulator for testing embedded firmware over a physical SPI bus. A Python API configures register values, SPI responses, and transaction behavior over UART.
</p>

<div class="overview-board-frame">
  <img class="overview-board-image" src="/assets/images/RH01T9k-overview.png" alt="RH01T9k SPI peripheral emulator connected to a microcontroller">
</div>

<p class="lead overview-after-image">
Built on the Tang Nano 9K FPGA, RH01T9k can replace an SPI sensor or peripheral during firmware testing, hardware-in-the-loop (HIL) testing, and automated hardware validation.
</p>

## Why emulate an SPI peripheral?

Physical sensors do not always provide the repeatable states, edge cases, or invalid responses needed for firmware testing.

RH01T9k lets tests provide controlled SPI responses such as:

- incorrect device IDs
- synthetic sensor data
- repeatable register states
- boundary and error conditions

## How it works

The MCU runs its normal firmware while RH01T9k replaces the target SPI peripheral.

<div class="diagram">
  MCU ⇄ SPI ⇄ RH01T9k ⇄ UART ⇄ Python
</div>

Python configures the emulated peripheral. The MCU then communicates with RH01T9k using normal SPI transactions.

MOSI and MISO transactions can also be captured for debugging and automated test verification.

## Current features

- SPI modes 0–3, tested up to 20 MHz
- Configurable SPI read/write command decoding
- Configurable address decoding
- 256-byte programmable register space
- Single and burst register access
- Configurable response delay
- Triggered SPI transaction capture

## Planned features

- Fault and error injection
- Command-map mode for custom SPI protocols
- GPIO interrupt and sideband signal emulation
