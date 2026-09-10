---
layout: layouts/docs.njk
tags: docs
navExclude: true
title: Register Read and Write Example
downloads:
  - name: 02_register_rw.py
    url: /assets/downloads/02_register_rw.py
  - name: 02_register_rw.c
    url: /assets/downloads/02_register_rw.c
---

<div class="eyebrow">Example02</div>

# SPI Register Read/Write

This example configures the RH01T9k as an SPI peripheral with configurable command-byte decoding and initial register values.
After setup, the SPI controller performs register reads and writes directly over the physical SPI bus. 

<div class="note"><strong>Note:</strong> Complete the [Ping Example](/examples/ping/) before continuing. Ping confirms that the computer can communicate with and configure the emulator board.</div>


## Hardware setup

* 1× RH01T9k SPI peripheral
* 1× computer
* 1× USB Type-C data cable
* 1× SPI controller, such as ESP32
* Jumper wires

Connect the SPI signals between the controller and RH01T9k as shown below.

```text
SPI Controller                    RH01T9k

CS        ----------------------> CS
SCLK      ----------------------> SCLK
MOSI      ----------------------> MOSI
MISO      <---------------------- MISO
GND       ----------------------- GND
```

### Step 1: Define the register protocol

`RegisterDevice()` defines the SPI command format the controller must use to access the emulated registers.

For this example, bit 7 selects read or write, bit 6 enables address auto-increment, and bits 5:0 contain the register address. These fields are user-defined and can be changed for a different SPI protocol.

```text
Bit:       7       6       5 ... 0
          R/W     NEXT     ADDRESS

bit 7 = 1   Read from a register
bit 7 = 0   Write to a register

bit 6 = 1   Move to the next register address after each byte
bit 6 = 0   Keep using the same register address

bits 5:0    Register address
```

`NEXT` represents auto-increment. When enabled, the register address advances after each data byte, allowing several neighboring registers to be accessed in one SPI transaction.

```python
from hil import RegisterDevice

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

```

For this configuration, example command bytes are:

```text
0x85 = read register 0x05
0x05 = write register 0x05

0xE0 = burst read starting at register 0x20
0x60 = burst write starting at register 0x20
```

<code>mode=0</code> selects SPI Mode 0. The emulator supports SPI Modes 0–3, but the controller and emulator must use the same mode.

<code>default_miso=0x00</code> defines the value placed on MISO when no register data is being returned, such as while the command byte is being received.

<code>response_delay_bytes=0</code> means the requested register value begins on the byte immediately following the command. Increasing this value inserts additional byte periods before the response.

### Step 2: Load starting register values

Optionally, define the initial values for the emulated registers.

Individual registers can be assigned directly using `register[address] = value`. 
Multiple consecutive registers can be initialized using `load()`. 

```python
registers[0x05] = 0x11          # Set one register: [address] = value
registers[0x06] = 0x22          # Set one register: [address] = value

registers.load(
    [0xAA, 0xBB, 0xCC, 0xDD],   # Set consecutive values
    start=0x20,                 # Starting register address
)
```

This produces the following register contents:

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

### Step 3: Apply the configuration

`emulate_registers()` sends the `RegisterDevice` settings and initial register values to the emulator board and enables its SPI. After this completes, the emulator is ready to respond to SPI transactions from the SPI controller. 

```python
from hil import HIL

PORT = "COM7"                             # Change to assigned serial port
BAUD = 115200                             # Must remain at 115200

with HIL(PORT, BAUD) as dev:
    dev.ping()                            # Verify connection
    dev.clear_errors()                    # Clear previous errors
    dev.spi.emulate_registers(registers)  # Apply configuration
```


### Step4: Send SPI transactions

After the Python configuration has been applied, an SPI controller can communicate directly with the emulated register device. If using the ESP32, download and run 02_register_rw.c for testing. 

<div class="note"><strong>Caution:</strong> In SPI Modes 1 and 3, configure a small chip-select pre-transaction delay before the first clock edge. In ESP32, use <code>cs_ena_pretrans = 2</code>. Without this delay, MISO data may be received one clock cycle late.</div>

Each SPI transaction begins with the configured command byte:

```text
command = R/W bit | NEXT bit | ADDRESS bits
```

The remaining MOSI bytes either carry write data or provide clock cycles so the controller can receive register data on MISO.

<div class="note"><strong>Caution:</strong> Configuration changes are applied between SPI transactions. Make sure chip select is high before starting or changing the emulator configuration. If CS remains low, the configuration request may wait and eventually time out.</div>

<div class="note"><strong>Caution:</strong> Keep the SPI controller and RH01T9k in the same SPI mode. A mode mismatch can produce incorrect data even when the wiring is correct.</div>


## Expected results

The following transfers show the expected MISO data returned by the emulated peripheral in response to the MOSI data sent by the SPI controller, using the RH01T9k configuration defined above.

<div class="note"><strong>Note:</strong> Each MOSI/MISO sequence shown below represents one complete SPI transaction. Keep CS asserted for the entire command and its associated data bytes. </div>


### Single-register read

To read the preloaded value at register `0x05`, the SPI master sends `0x85`: read bit `0x80` combined with address `0x05`.

SPI master then sends one dummy byte. This additional byte provides the clock cycles required for the SPI slave to return the register value.

```text
MOSI:  85  00
MISO:  00  11
```

The first MISO byte is the configured default `0x00` while the peripheral receives the command. The second byte is `0x11`, the value stored at register `0x05`.


### Burst read with auto-increment

To read registers `0x20` through `0x23` in one transaction, the SPI master enables both the read bit (`0x80`) and auto-increment bit (`0x40`) and supplies the starting address (`0x20`).

Together these fields form command `0xE0`.

The following 0x00 bytes are dummy bytes sent by MOSI to provide the clock cycles needed for the peripheral to return each register value on MISO.

```text
MOSI:  E0  00  00  00  00
MISO:  00  AA  BB  CC  DD
```

The first returned register value is `0xAA` from address `0x20`. After each byte, the SPI slave advances to the next address, returning `0x21`, `0x22`, and `0x23` without requiring another command.

This type of transfer is useful for multi-byte measurements or blocks of neighboring registers.


### Single-register write

To write to register `0x05`, the SPI master sends command `0x05`. Bit 7 is 0, which selects a write, and the lower bits select address `0x05`.

The next MOSI byte `0x77` is the value to store in the register.

```text
MOSI:  05  77
MISO:  00  00
```

After the transaction, register `0x05` contains `0x77`. MISO is not used for data during this write.

A following read should confirm that the register was updated:

```text
MOSI:  85  00
MISO:  00  77
```


### Burst write with auto-increment

To write several consecutive registers, the SPI master sends the write command with the auto-increment bit enabled.

For a starting address of `0x20`, the command is `0x60`.

```text
MOSI:  60  11  22  33  44
MISO:  00  00  00  00  00
```

After each data byte, the register address advances automatically:

```text
Address    Value
-------    -----
0x20       0x11
0x21       0x22
0x22       0x33
0x23       0x44
```

A later burst read from `0x20` should therefore return:

```text
MOSI:  E0  00  00  00  00
MISO:  00  11  22  33  44
```


### Repeated write without auto-increment

If the SPI master starts a write to register `0x20` without setting the NEXT bit, the address remains fixed at `0x20` for the entire transaction.

For example:

```text
MOSI:  20  11  22  33  44
MISO:  00  00  00  00  00
```

The writes occur sequentially to the same address:

```text
0x20 = 0x11
0x20 = 0x22
0x20 = 0x33
0x20 = 0x44
```

Each new byte overwrites the previous value, so that the final value stored at `0x20` is `0x44`. Registers `0x21`, `0x22`, and `0x23` remain unchanged.

### Repeated read without auto-increment

If the SPI master sends a read command for register 0x20 without setting the NEXT bit, the address remains fixed at 0x20 for the entire transaction.

Four dummy bytes provide clocks for four returned values:

```text
MOSI:  A0  00  00  00  00
MISO:  00  44  44  44  44
```

The SPI slave reads register `0x20` for every response byte. Since the previous test left `0x44` at that address, the same value is returned four times.
