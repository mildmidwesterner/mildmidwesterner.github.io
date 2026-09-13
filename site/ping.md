---

layout: layouts/docs.njk
tags: docs
navExclude: true
title: Ping Example
description: Verify USB serial communication between your computer and RH01T9k with the Python API Ping example.
---

<div class="eyebrow">Example 01</div>

# Ping

Use Ping to verify communication between the computer and RH01T9k over the USB serial control connection.

A successful Ping confirms that the board is connected and responding to commands from the Python API.

## Connect the board

Connect RH01T9k to the computer using a USB Type-C data cable.

<div class="note"><strong>Note:</strong> Use a USB cable that supports data. A charge-only cable can power the board but cannot provide serial communication.</div>

Close any serial terminal, IDE monitor, or other program using the same serial port.

## Find the serial port

On Windows, open **Device Manager → Ports (COM & LPT)** and identify the port assigned to the board, for example:

```text
COM7
```

On macOS, compare the output of:

```sh
ls /dev/cu.*
```

before and after connecting the board. The new device may appear as:

```text
/dev/cu.usbserial-XXXX
```

## Run Ping

Set `PORT` to the serial port assigned to the board.

The UART control baud rate is fixed at `115200`. This is separate from the SPI clock rate.

```python
from hil import HIL

PORT = "COM7"      # Set assigned serial port
BAUD = 115200      # Required — do not change


with HIL(PORT, BAUD) as dev:
    dev.ping()
    print("PING OK")

    status = dev.get_status()
    print(f"status = 0x{status.raw:04X}")
```

## Expected result

Successful communication produces output similar to:

```text
PING OK
status = 0x8000
```

`PING OK` confirms that RH01T9k responded to the Python API.

The status value may vary depending on the current board state.
