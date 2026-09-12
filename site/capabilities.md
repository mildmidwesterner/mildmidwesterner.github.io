---
layout: layouts/docs.njk
tags: docs
title: API Reference
nav: API Reference
---

<div class="eyebrow">Python API</div>

# Python API Guide
A reference for the Python API calls available for controlling RH01T9k.

## 1. Create a board connection

```python
from hil import HIL

board = HIL(port = "COM7", baudrate = 115200, timeout=2.0)
```

`HIL` creates the top-level API object. It owns the serial control connection and exposes SPI functionality through `board.spi`.

Parameters:

- `port` is the board's serial-port name, such as `"COM7"` on Windows or `"/dev/cu.usbserial-XXXX"` on macOS.
- `baudrate` defaults to 115,200.
- `timeout` is the overall command timeout in seconds. It also bounds automatic retries when a hardware operation is temporarily busy.

The current RedHors01T9k build uses a fixed **115,200-baud** control link. Changing the Python value does not reconfigure the board. A mismatch normally produces a timeout, framing error, or CRC error.

The constructor does not open the serial port. Call `open()` or use a `with` statement.

## 2. Control the serial connection

```python
board = HIL("COM7")
board.open()

try:
    board.ping()
finally:
    board.close()
```

`open()` opens the configured serial port and clears stale bytes from its host-side input and output buffers. Calling it while already open is harmless. It returns the same `HIL` object.

`close()` releases the serial port. Calling it more than once is safe.

Only one process should own the board's serial port at a time. Close serial terminals, IDE monitors, and other test programs before connecting.

## 3. Open and close the connection automatically

```python
with HIL("COM7", 115200) as board:
    board.ping()
```

The context manager calls `open()` on entry and `close()` on exit, including when an exception occurs. This is the recommended connection pattern.

## 4. Verify end-to-end communication

```python
with HIL("COM7") as board:
    assert board.ping() is True
```

`ping()` sends a framed command and waits for the matching board response. Success verifies the serial port, UART path, packet framing, CRC handling, command routing, and response path.

A visible serial port proves only that the operating system detected a USB serial device. A successful ping proves that RedHors01T9k is responding to this API.

`ping()` does not clear old errors and does not prove that every status flag is healthy. Follow it with `get_status()` when startup diagnostics matter.

## 5. Inspect board health and SPI readiness

```python
status = board.get_status()

print(f"raw status: 0x{status.raw:04X}")
print("SPI ready:", status.spi_armed)
print("CS asserted:", status.spi_cs_low)
```

`get_status()` returns a `Status` object containing the 16-bit status word. Each named `Status` property corresponds to one bit in `status.raw`. Bits 7–9 currently have no named status property. 

| Bit| Property | Meaning |
|---:|---|---|
| 0 | `uart_framing_error` | A serial character did not have valid UART framing. Check for a baud mismatch or poor connection. |
| 1 | `uart_overrun_error` | Serial bytes arrived faster than the board could retain them. Ensure that only one host controls the port. |
| 2 | `packet_rx_crc_error` | A received host packet failed CRC validation. The damaged command must not be trusted. |
| 3 | `packet_rx_length_error` | A received packet declared an unsupported payload length. Check package compatibility and the serial link. |
| 4 | `packet_tx_length_error` | The board attempted to construct an invalid-length response. Preserve a reproducible case and treat it as an implementation fault. |
| 5 | `unsupported_command` | The host sent a command not supported by the installed board image. Check package and board-image compatibility. |
| 6 | `invalid_command_length` | A known command arrived with an incorrect payload length. Check package compatibility or link corruption. |
| 10 | `spi_command_decode_error` | An external transaction's command byte matched neither the configured read nor write pattern. |
| 11 | `spi_capture_overflow` | At least one capture event was lost or arrived after capture storage was full. |
| 12 | `spi_enable_requested` | Python has requested that SPI emulation be enabled. |
| 13 | `spi_armed` | The SPI interface is ready to participate in an external transaction. |
| 14 | `spi_cs_low` | The physical active-low chip-select input is currently asserted. |
| 15 | `spi_shadow_ready` | The active response image is ready for another host register operation. |

Error properties are sticky. They report that a condition has occurred since the applicable clear operation or board reset, not necessarily that it is occurring at the instant of the read.

## 6. Clear sticky diagnostic flags

```python
board.clear_errors()
```

`clear_errors()` clears the sticky `uart_framing_error`, `uart_overrun_error`, `packet_rx_crc_error`, `packet_rx_length_error`, `packet_tx_length_error`, `unsupported_command`, `invalid_command_length`, and `spi_command_decode_error` properties. 

Capture-buffer contents and the buffer's own overflow state have a separate lifecycle. For a completely clean capture run, use both calls:

```python
board.spi.capture_clear()
board.clear_errors()
```

## 7. Read the board timebase

```python
timestamp = board.get_timestamp()

print(timestamp.raw_ticks)
print(timestamp.seconds)
print(timestamp.milliseconds)
print(timestamp.microseconds)
print(timestamp.nanoseconds)
```

`get_timestamp()` returns a `Timestamp`, representing the current 48-bit board counter.

The counter uses the 27 MHz system clock:

- 27,000,000 ticks per second
- Approximately 37.037 ns per tick
- 48-bit range from `0` through `2^48 - 1`
- Wraparound after approximately 120.7 days

The properties return floating-point conversions. `raw_ticks` preserves the exact counter value. `int(timestamp)` also returns the raw ticks.

The timestamp measures board uptime from reset. it is not UTC, local time, or automatically synchronized with the computer clock. 

## 8. Calculate wrap-safe elapsed time

```python
start = board.get_timestamp()

# Perform the operation being measured.

finish = board.get_timestamp()
elapsed = finish - start

print(elapsed.ticks)
print(elapsed.microseconds)
```

Subtracting two `Timestamp` objects returns a `Duration`.

`Duration` provides:

- `ticks`
- `seconds`
- `milliseconds`
- `microseconds`
- `nanoseconds`

The API cannot distinguish multiple complete 120.7-day wraps between two observations. For normal test and capture intervals this ambiguity is irrelevant.

## 9. Describe an SPI peripheral

```python
from hil import RegisterDevice

sensor = RegisterDevice(
    mode=0,
    default_miso=0x00,
    read_mask=0x80,
    read_value=0x80,
    write_mask=0x80,
    write_value=0x00,
    address_mask=0x7F,
    address_shift=0,
    auto_increment_mask=0x80,
    auto_increment_value=0x80,
    response_delay_bytes=0,
    fill=0x00,
)
```

`RegisterDevice` is a declarative description plus a complete 256-byte initial register image. It does not communicate with the board until passed to `emulate_registers()`.

All byte-valued constructor parameters accept 0 through 255. Invalid modes, shifts, ranges, or value/mask combinations raise `ValueError` before board communication.

### SPI mode

`mode` accepts 0, 1, 2, or 3.

| Mode | CPOL | CPHA | Operating note |
|---:|---:|---:|---|
| 0 | 0 | 0 | First MISO bit is prepared while SCLK is idle. |
| 1 | 0 | 1 | Requires non-zero CS setup time before the first SCLK edge. |
| 2 | 1 | 0 | First MISO bit is prepared while SCLK is idle. |
| 3 | 1 | 1 | Requires non-zero CS setup time before the first SCLK edge. |

The maximum guaranteed SCLK rate is **20 MHz in every mode**. 

For SPI Modes 1 and 3, add a CS-to-SCLK setup delay before the first clock edge. One full SCLK period is a conservative setting.

A continuously low chip select is treated as one SPI transaction. For each transaction, assert CS, transfer a whole number of bytes, then deassert CS. Keep CS low through the final clock edge, and make sure it goes high for a real interval before the next transaction begins.

### Default MISO and response delay

`default_miso` is returned whenever register response data is not active. The first MISO byte of every transaction is the default byte while the first MOSI byte is decoded as the command.

For a zero-delay read, register data starts during the next byte. `response_delay_bytes` inserts additional default-MISO byte periods before register data begins. It accepts values from 0 through 255.

### Read and write matching

A command is a read when:

```text
(command & read_mask) == read_value
```

A command is a write when:

```text
(command & write_mask) == write_value
```

`read_value` may contain bits only inside `read_mask`. The same rule applies to the write pair. A command matching neither rule sets `spi_command_decode_error`.

For the common convention where bit 7 chooses direction:

```python
read_mask=0x80,
read_value=0x80,
write_mask=0x80,
write_value=0x00,
```

### Address extraction

`address_mask` selects address bits from the command and `address_shift` shifts that field right. `address_shift` accepts 0 through 7.

For a seven-bit register address in command bits 6:0:

```python
address_mask=0x7F,
address_shift=0,
```

### Auto-increment matching

When `auto_increment_mask` is nonzero, sequential access is selected when:

```text
(command & auto_increment_mask) == auto_increment_value
```

This allows one transaction to advance through consecutive register addresses. Set `auto_increment_mask=0x00` when conditional auto-increment is not needed.


## 10. Set register values

Assign a value directly to a register address:

```python
sensor[0x00] = 0xD1
sensor[0x03] = 0x10
sensor[0x12] = 0x00
```

This produces register contents such as:

```text
Address    Value
-------    -----
0x00       0xD1
0x03       0x10
0x12       0x00
```

Reading an address returns its currently assigned value:

```python
chip_id = sensor[0x00]
```

These operations update the local `RegisterDevice` image. They do not change an already running board until a later `emulate_registers(sensor)` call loads the image.

## 11. Set consecutive register values

Use `load()` to assign several neighboring registers at once:

```python
sensor.load(
    [0x11, 0x22, 0x33, 0x44],
    start=0x20,
)
```

This produces:

```text
Address    Value
-------    -----
0x20       0x11
0x21       0x22
0x22       0x33
0x23       0x44
```

Each value is assigned to the next register address starting at `start`. The range must fit within the 256-byte address space.

## 12. Inspect register contents

```python
complete_image = sensor.image()

for address, value in sensor.items():
    print(f"0x{address:02X}: 0x{value:02X}")
```

`image()` returns an immutable `bytes` copy containing all 256 registers. `items()` iterates over all 256 `(address, value)` pairs in ascending address order.


## 13. Activate a peripheral

Use `emulate_registers()` to send the `RegisterDevice` configuration and register values to the board, then enable the SPI emulator. 

```python
board.spi.emulate_registers(sensor)
```

This convenience call performs the setup sequence:

1. Configures the SPI mode and command-byte format.
2. Loads all 256 register values.
3. Makes the loaded register values active.
4. Enables the SPI interface.

After `emulate_registers()` completes, the SPI controller can communicate with the emulated peripheral using the configured register protocol.

## 14. Read a register from the peripheral 

`read_register()` returns one byte from the active register image. This is a host-side inspection operation. It does not generate an external SPI transaction.

```python
value = board.spi.read_register(0x00)
```

The address must be 0 through 255. The API verifies that the response contains the requested address and expected payload size, raising `ProtocolError` if it does not.

## 15. Stage one register update

Use `stage_register()` to prepare a change to one register on an emulator that is already configured and running. This is different from assigning a value with `RegisterDevice[address] = value`, which only changes the `RegisterDevice` before it is loaded onto the board with `emulate_registers()`.

```python
board.spi.stage_register(0x20, 0x5A)
```

The new value is written to the staging area and is not yet visible to the SPI controller. Call `commit()` when you want the staged value to become active.

```python
board.spi.commit()
```

## 16. Stage consecutive register updates

Use `stage_block()` to prepare changes to several consecutive registers on an emulator that is already configured and running. This is different from `RegisterDevice.load()`, which only sets values in the `RegisterDevice` before it is loaded onto the board with `emulate_registers()`.

```python
board.spi.stage_block(
    0x30,
    [0x10, 0x20, 0x30, 0x40],
)
```

This stages:

```text
0x30 = 0x10
0x31 = 0x20
0x32 = 0x30
0x33 = 0x40
```

The staged values remain hidden from the SPI controller until `commit()` is called.

```python
board.spi.commit()
```

Use `stage_block()` when several register values should become visible at the same time.

## 17. Publish all staged values together

```python
board.spi.stage_register(0x10, 0xAA)
board.spi.stage_block(0x20, [0x01, 0x02, 0x03])
board.spi.commit()
```

`commit()` switches the complete staged image into service at once. All staged values become visible together at a safe chip-select-idle boundary. 

If an SPI transaction is active, the update remains pending until chip select goes high and the transaction ends.

## 18. Stage and commit one byte

```python
board.spi.write_register(0x20, 0x5A)
```

This convenience call performs `stage_register()` followed by `commit()`. It is simple and safe, but repeated calls publish each byte separately.

For multiple related values, use `stage_block()` plus one `commit()`, `write_block()`, or `update_atomic()`.

## 19. Stage and commit consecutive bytes

```python
board.spi.write_block(0x30, [0x10, 0x20, 0x30, 0x40])
```

This convenience call updates a running emulator by staging the full block and publishing it with one commit. The external controller sees either the old block or the new block, not a partially loaded intermediate state.

## 20. Update a validated multi-byte register block

`update_atomic()` updates several consecutive registers on a running emulator and commits them together.

```python
board.spi.update_atomic(
    0x12,
    [0x10, 0x20, 0x30, 0x40, 0x50, 0x60],
)
```

Like `write_block()`, the values are staged first and then made active in one commit.

The difference is that `update_atomic()` can optionally validate the update against a configured register range.

```python
board.spi.configure_atomic_window(0x12, 6)

board.spi.update_atomic(
    0x12,
    six_byte_sample,
)
```

Here, the allowed update range is `0x12` through `0x17`. An `update_atomic()` call must stay completely within that range. If no atomic window is configured, `update_atomic()` behaves similarly to `write_block()` for any valid register range.

## 21. Configure SPI transaction capture

`capture_configure()` defines which SPI activity should be recorded and when capture should stop. It can trigger on selected command bytes and limit the capture by transaction count, byte count, or total stored records.

```python
board.spi.capture_configure(
    triggers=[(0xFF, 0x92)],
    transaction_limit=8,
    byte_limit=0,
    record_limit=512,
)
```

`triggers` accepts up to four `(mask, value)` pairs. The rules examine the first MOSI byte of each transaction. Capture starts when any rule matches:

```text
(first_mosi_byte & mask) == (value & mask)
```

Examples:

```python
triggers=[
    (0xFF, 0x92),  # exact command 0x92
    (0xF0, 0xA0),  # any command from 0xA0 through 0xAF
]
```
With an empty trigger list, capture begins immediately after capture_start(). If trigger rules are configured, capture begins when a trigger matches, and the triggering transaction is included as transaction one.

`transaction_limit` is the maximum number of SPI transactions to record. Set to 0 to disable this limit.
`byte_limit` is the maximum number of transferred SPI bytes to use as a stop condition. Set to 0 to disable this limit.
`record_limit` is the maximum number of capture records that can be stored before capture stops. Set to 0 to disable the configured record-limit stop condition.

Regardless of the configured limits, the capture buffer has a hard physical capacity of 512 records. Configuration is rejected with `ValueError` if there are more than four rules, a malformed rule, an out-of-range value, or a record limit above 512.

## 22. Start SPI transaction capture

```python
board.spi.capture_start()
```

With trigger rules, capture enters the armed state and waits for a matching first command byte. Without trigger rules, it begins recording immediately.

Start fails as busy if capture is already active or armed, the capture buffer is full, or an external transaction is active. 

Recommended sequence:

```python
board.spi.capture_clear()
board.clear_errors()
board.spi.capture_configure(
    triggers=[(0xFF, 0x92)],
    transaction_limit=8,
    record_limit=512,
)
board.spi.capture_start()
```

## 23. Stop SPI transaction capture

```python
board.spi.capture_stop()
```

`capture_stop()` manually ends capture while preserving the records already stored.

A manual stop is not required when `transaction_limit`, `byte_limit`, or `record_limit` is configured and the capture reaches that limit automatically.

Use `capture_stop()` when no automatic stop condition is defined, or when you want to end capture before a configured limit is reached.

## 24. Inspect SPI transaction capture status

Use `capture_status()` to check whether capture is armed, triggered, complete, full, or holding valid records.

```python
status = board.spi.capture_status()

print("armed:", status.armed)
print("triggered:", status.triggered)
print("done:", status.done)
print("records:", status.count, "/", status.depth)
```

The returned `CaptureStatus` contains:

| Property | Meaning |
|---|---|
| `active` | The capture buffer is currently accepting records. |
| `armed` | Capture is armed and, when triggers are configured, waiting for a match. |
| `triggered` | A trigger has matched. Immediate capture reports triggered from the start. |
| `done` | Capture stopped automatically because a transaction, byte, or record limit was reached. |
| `full` | All 512 physical capture-record slots are occupied. |
| `empty` | No capture records are currently retained. |
| `loss_or_overflow` | At least one capture event was lost or the capture buffer overflowed. |
| `count` | Number of capture records currently retained. |
| `depth` | Physical capture capacity, currently 512 records. |
| `transaction_count` | Number of captured transactions completed. |
| `byte_count` | Number of captured SPI byte records processed. |


## 25. Reset SPI transaction capture

Use `capture_clear()` to stop the current capture and reset its retained state.

```python
board.spi.capture_clear()
```
After `capture_clear()`:

| Property | Reset state |
|---|---|
| `active` | `False` |
| `armed` | `False` |
| `triggered` | `False` |
| `done` | `False` |
| `full` | `False` |
| `empty` | `True` |
| `count` | `0` |
| `transaction_count` | `0` |
| `byte_count` | `0` |

After clearing, the capture buffer is treated as empty and previous records are no longer accessible through the capture API.

For a completely clean diagnostic state, also clear board-wide error flags:

```python
board.spi.capture_clear()
board.clear_errors()
```
`clear_errors()` is separate because board-wide event-loss flags are not part of the SPI capture state.

## 26. Retrieve capture records

Use `capture_read()` to retrieve capture records by index:

```python
records = board.spi.capture_records()

if records:
    origin = records[0].timestamp

    for record in records:
        elapsed = record.timestamp - origin

        print(
            f"{record.index:4d}",
            f"{record.type_name:5s}",
            f"t={elapsed.microseconds:10.3f} us",
            f"MOSI=0x{record.mosi:02X}",
            f"MISO=0x{record.miso:02X}",
            f"lost={record.transaction_lost}",
        )
```

`capture_read()` is non-destructive and returns a `CaptureRecord`.

A `CaptureRecord` contains:

- `index` — capture-buffer index
- `event_type` — numeric event code
- `type_name` — `"start"`, `"byte"`, `"end"`, or `"unknown"`
- `timestamp` — event timestamp using the board's 27 MHz timebase
- `mosi` — byte sent by the SPI controller
- `miso` — byte returned by the RH01T9k
- `transaction_lost` — indicates an incomplete retained transaction

The event types are:

- START (`event_type == 0`) — chip select begins a transaction
- BYTE (`event_type == 1`) — one complete MOSI/MISO byte pair is recorded
- END (`event_type == 2`) — chip select ends the transaction

