---

layout: layouts/docs.njk
tags: docs
navExclude: true
title: SPI Register Read and Write Example
description: Configure RH01T9k as a register-based SPI peripheral and test single, burst, and repeated register reads and writes.
---

<div class="eyebrow">Example 02</div>

# SPI Register Read/Write

This example configures RH01T9k as a register-based SPI peripheral so you can test an SPI controller without a physical sensor. The controller performs single and burst register reads and writes over a real SPI bus.

<div class="note"><strong>Note:</strong> Complete the <a href="/ping/">Ping Example</a> first to verify the USB serial control connection.</div>

## Hardware setup

Connect the SPI controller to RH01T9k:

```text
SPI Controller                    RH01T9k

CS        ----------------------> CS
SCLK      ----------------------> SCLK
MOSI      ----------------------> MOSI
MISO      <---------------------- MISO
GND       ----------------------- GND
```

Use 3.3 V logic and configure both devices for the same SPI mode.

## Register protocol

`RegisterDevice()` defines how the SPI command byte is interpreted.

For this example:

```text
Bit:       7       6       5 ... 0
          R/W     NEXT     ADDRESS
```

* bit 7 = `1`: read
* bit 7 = `0`: write
* bit 6 = `1`: auto-increment the register address
* bits 5:0: register address

Example commands:

```text
0x85    Read register 0x05
0x05    Write register 0x05
0xE0    Burst read starting at 0x20
0x60    Burst write starting at 0x20
```

## Configure the emulator

Set `PORT` to the serial port assigned to RH01T9k.

```python
from hil import HIL, RegisterDevice

PORT = "COM7"      # Set assigned serial port
BAUD = 115200      # Required — do not change


registers = RegisterDevice(
    mode=0,
    default_miso=0x00,

    read_mask=0x80,
    read_value=0x80,

    write_mask=0x80,
    write_value=0x00,

    address_mask=0x3F,
    address_shift=0,

    auto_increment_mask=0x40,
    auto_increment_value=0x40,

    response_delay_bytes=0,
)


registers[0x05] = 0x11
registers[0x06] = 0x22

registers.load(
    [0xAA, 0xBB, 0xCC, 0xDD],
    start=0x20,
)


with HIL(PORT, BAUD) as dev:

    dev.ping()
    dev.clear_errors()

    print()
    print("Configuring register emulator...")

    dev.spi.emulate_registers(registers)

    print("Startup register values:")
    print("  reg05 = 11")
    print("  reg06 = 22")
    print("  reg20 = AA")
    print("  reg21 = BB")
    print("  reg22 = CC")
    print("  reg23 = DD")
    print()
```

The initial register contents are:

```text
Address    Value
-------    -----
0x05       0x11
0x06       0x22
0x20       0xAA
0x21       0xBB
0x22       0xCC
0x23       0xDD
```

`mode=0` selects SPI Mode 0.

`default_miso=0x00` defines the MISO value returned while the command byte is being received.

`response_delay_bytes=0` returns register data beginning with the byte immediately after the command.

## Send SPI transactions

After `emulate_registers()` completes, the SPI controller communicates directly with RH01T9k over the physical SPI bus.

An ESP32 SPI master example is available on GitHub:

[ESP32 SPI master example](https://github.com/mildmidwesterner/esp32-spi-master)

The included C firmware has been tested on a **Seeed Studio XIAO ESP32-S3** and can be used to exercise the single-register and burst read/write transactions shown below.

<div class="note"><strong>Note:</strong> Keep CS asserted for the entire command and data transfer, and return CS high between transactions.</div>

<div class="note"><strong>Note:</strong> For SPI Modes 1 and 3, provide a CS-to-SCLK setup delay before the first clock edge. On ESP32, <code>cs_ena_pretrans = 2</code> can be used for this example.</div>

## Expected SPI transactions

### Single-register read

Read register `0x05`:

```text
MOSI:  85  00
MISO:  00  11
```

`0x85` selects a read from address `0x05`. The following byte provides the clock cycles used to return `0x11`.

### Burst read

Read registers `0x20` through `0x23` with auto-increment enabled:

```text
MOSI:  E0  00  00  00  00
MISO:  00  AA  BB  CC  DD
```

The register address advances after each returned byte.

### Single-register write

Write `0x77` to register `0x05`:

```text
MOSI:  05  77
MISO:  00  00
```

A following read confirms the new value:

```text
MOSI:  85  00
MISO:  00  77
```

### Burst write

Write four consecutive registers starting at `0x20`:

```text
MOSI:  60  11  22  33  44
MISO:  00  00  00  00  00
```

The resulting register values are:

```text
0x20 = 0x11
0x21 = 0x22
0x22 = 0x33
0x23 = 0x44
```

A burst read then returns:

```text
MOSI:  E0  00  00  00  00
MISO:  00  11  22  33  44
```

## Address behavior without auto-increment

When the `NEXT` bit is not set, the register address remains fixed for the entire transaction.

Repeated write:

```text
MOSI:  20  11  22  33  44
MISO:  00  00  00  00  00
```

All four values are written to register `0x20`, so its final value is `0x44`.

Repeated read:

```text
MOSI:  A0  00  00  00  00
MISO:  00  44  44  44  44
```

The same register is returned for each response byte.
