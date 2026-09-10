---
layout: layouts/docs.njk
tags: docs
title: Get Hardware
nav: Get Hardware
navExclude: true
downloads:
  - name: hil_bmi160.fs
    url: /assets/downloads/hil_bmi160.fs
---

<div class="eyebrow">Getting Started</div>

# Get Hardware

## Option 1: Request a RH01T9k

Email [mildmidwesterner@gmail.com](mailto:mildmidwesterner@gmail.com) with a short description of your use case. I currently have a limited number of boards available and can ship at no cost for testing.

## Option 2: Program a Tang Nano 9K

You can also program your own Tang Nano 9K using the bitstream provided on this page. Download `hil_bmi160.fs` and program the board using the GOWIN programming tools.

<div class="note"><strong>Caution:</strong> This bitstream is specifically built for the Tang Nano 9K. Do not program it onto a different FPGA board.</div>


## Option 3: Build from Verilog source

The FPGA source repository is planned for a future release. For immediate access or questions, email [mildmidwesterner@gmail.com](mailto:mildmidwesterner@gmail.com).

## Next step

Once you have a programmed board, continue to [Hardware Setup](/hardware-setup/) for SPI wiring, pin assignments, voltage requirements, and operating limits.
