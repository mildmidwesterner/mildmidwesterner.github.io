---

layout: layouts/docs.njk
tags: docs
title: Get Hardware
nav: Get Hardware
navExclude: true
description: Build the open-source RH01T9k FPGA design or program a Tang Nano 9K with the provided bitstream.

downloads:

  - name: hil_bmi160.fs
    url: /assets/downloads/hil_bmi160.fs

---

<div class="eyebrow">Getting Started</div>

# Get Hardware

RH01T9k is open source. Choose one of these two ways to get started:

1. Use the open-source FPGA design
2. Program a Tang Nano 9K using the provided bitstream

## Option 1: Use the FPGA source

The FPGA source is available on GitHub:

[RH01T9k FPGA source](https://github.com/mildmidwesterner/programmable-spi-slave-emulator/tree/main/fpga)

The current project targets the Tang Nano 9K, but the RTL can be ported to other FPGA boards. Board-specific changes may include the system clock configuration, pin assignments, and corresponding timestamp settings in the Python API.

## Option 2: Program the provided bitstream

If you do not want to build the FPGA design from source, you can use the provided prebuilt bitstream:

[`hil_bmi160.fs`](/assets/downloads/hil_bmi160.fs)

Program the `.fs` file onto a Tang Nano 9K using the GOWIN programming tools.

<div class="note"><strong>Important:</strong> This bitstream is built specifically for the Tang Nano 9K. Do not program it onto a different FPGA board.</div>

## Next step

Once the board is programmed, continue to [Hardware Setup](/hardware-setup/) for SPI wiring, pin assignments, voltage requirements, and operating limits.
