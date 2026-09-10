---
layout: layouts/docs.njk
tags: docs
title: Quick Start
nav: Quick Start
navExclude: true
downloads:
  - name: redhorse_hil-0.1.0-py3-none-any.whl
    url: /assets/downloads/redhorse_hil-0.1.0-py3-none-any.whl
---

<div class="eyebrow">Getting Started</div>

# Quick Start

Install the Python API, connect the RH01T9k to the computer, and verify communication.

## 1. Connect the board

Connect the RH01T9k to the computer using a USB Type-C data cable. Confirm that the board powers on, then wait a few seconds for the computer to detect the serial port.

<div class="note"><strong>Note:</strong> A charge-only USB cable can power the board but cannot transfer data. Use a USB cable that supports data.</div>

<div class="note"><strong>Note:</strong> Close any serial terminal, IDE monitor, or other program that may already be using the board's serial port.</div>


## 2. Install the Python API

RedHorse HIL supports Python 3.9 and newer. The package installs as `redhorse-hil` and imports in Python as `hil`.

### Option 1: Install with pip

The package is available from PyPI:

```bash
python -m pip install redhorse-hil
```

### Option 2: Install the downloadable wheel

Alternatively, download `redhorse_hil-0.1.0-py3-none-any.whl` from this page, then run:

```bash
python -m pip install redhorse_hil-0.1.0-py3-none-any.whl
```

The wheel installs the API and its required Python dependencies.


## 3. Find the serial port

Identify the serial port assigned to the RH01T9k.

Examples:

```text
Windows:  COM7
Linux:    /dev/ttyUSB0
macOS:    /dev/cu.usbserial-...
```

The exact name depends on the operating system and connected USB-UART interface.


## 4. Run Ping

Create a Python script:

```python
from hil import HIL

PORT = "COM7"      # Change to assigned serial port
BAUD = 115200      # Must remain at 115200

with HIL(PORT, BAUD) as board:
    board.ping()
    print("PING OK")

    status = board.get_status()
    print(f"status = 0x{status.raw:04X}")
```

Change `PORT` to the assigned serial port.

Keep `BAUD` at `115200`. This is the fixed serial control rate used by the board.

Run the script:

```bash
python ping.py
```

A successful connection should print:

```text
PING OK
status = 0x....
```

If Ping succeeds, the Python API can communicate with the RH01T9k and the board is ready to configure for SPI emulation.


## Next steps

Continue with the examples to:

- configure an emulated SPI register device
- set initial register values
- update registers while the emulator is running
- capture SPI transactions
- configure capture triggers and limits

See [Hardware Setup](/hardware-setup/) before connecting an SPI controller.
