---
layout: layouts/docs.njk
tags: docs
navExclude: true
title: Ping Example
download: /assets/downloads/01_ping.py
downloadName: 01_ping.py
---

<div class="eyebrow">Example01</div>

# Ping

Use Ping to confirm that the computer can communicate with the emulator board over USB before running an SPI test. 

A successful Ping verifies that the board is connected, responding, and ready to receive commands from the Python API.

## Hardware setup

- 1× RH01T9k SPI emulator
- 1× computer
- 1× USB Type-C data cable

Connect the board to the computer with the USB Type-C cable. Confirm that the board powers on. 

<div class="note"><strong>Caution:</strong> Close any serial terminal, IDE monitor, or other program that may already be using the board's connection.</div>

<div class="note"><strong>Caution:</strong> A charge-only USB cable can power the board but cannot transfer data. </div>

## Find the serial port

On Windows, open **Device Manager → Ports (COM & LPT)** and find the device added when the board was connected. It may look like `USB Serial Device (COM7)`.

On macOS, run this command before and after connecting the board:

```sh
ls /dev/cu.*
```

Use the newly listed `/dev/cu.*` path, such as `/dev/cu.usbserial-XXXX`.

## Run the test

Set the port for your board and keep the baud rate at `115200`:

```python
from hil import HIL

PORT = "COM7"
BAUD = 115200

with HIL(PORT, BAUD) as dev:
    dev.ping()
    print("PING OK")
    
    status = dev.get_status()
    print(f"status = 0x{status.raw:04X}")
```

The baud rate is the physical UART speed between the computer and the emulator board. It is not the SPI clock rate. 

<div class="note"><strong>Caution:</strong> Keep the baud rate set to 115200. </div>

<div class="note"><strong>Caution:</strong> Confirm that the selected port belongs to the emulator board. </div>

<div class="note"><strong>Note:</strong> If the status reports communication errors, clear the errors and run Ping again before continuing with SPI tests.</div>

## Expected result

Successful communication produces output similar to:

```text
PING OK
status = 0x8000
```

`PING OK` confirms the emulator board is connected and responding to commands from the Python API. 

The status value may change depending on the current board state. 
