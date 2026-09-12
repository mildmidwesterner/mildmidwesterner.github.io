---

layout: layouts/docs.njk
tags: docs
navExclude: true
title: SPI Transaction Capture Example
---

<div class="eyebrow">Example 03</div>

# SPI Transaction Capture

RH01T9k can record SPI transactions directly from the physical bus, including MOSI, MISO, transaction boundaries, and timestamps.

Capture can begin immediately or wait until the first MOSI byte matches a configured trigger.

Example capture:

```text
   0  start  t=     0.000 us  MOSI=0x00  MISO=0x00  lost=False
   1  byte   t=     1.185 us  MOSI=0x60  MISO=0x00  lost=False
   2  byte   t=     4.889 us  MOSI=0x11  MISO=0x00  lost=False
   3  end    t=     8.630 us  MOSI=0x00  MISO=0x00  lost=False
```

The capture buffer has a physical capacity of 512 records and is not an unlimited streaming trace.

## Configure capture

`capture_configure()` defines the trigger conditions and capture limits.

```python
dev.spi.capture_configure(
    triggers=[
        (0xFF, 0x60),
        (0xFF, 0x85),
        (0xFF, 0xE0),
    ],
    transaction_limit=10,
    record_limit=512,
)
```

This configuration waits for a transaction whose first MOSI byte is `0x60`, `0x85`, or `0xE0`.

Only the first completed MOSI byte after CS is asserted is tested against the trigger rules. For register-based protocols, this is normally the command byte.

Each trigger is a `(mask, value)` pair:

```text
(first_mosi_byte & mask) == (value & mask)
```

For example:

```python
triggers=[(0xF0, 0xA0)]
```

matches commands from `0xA0` through `0xAF`.

<div class="note"><strong>Note:</strong> Up to four trigger rules can be configured.</div>

To begin capturing immediately, use:

```python
triggers=[]
```

## Capture limits

Capture can stop automatically using:

* `transaction_limit` — stop after a specified number of completed SPI transactions
* `byte_limit` — stop after the transaction containing the specified number of captured bytes
* `record_limit` — stop after a specified number of stored capture records

A value of `0` disables that limit.

The physical capture depth remains 512 records even when `record_limit=0`.

## Start and stop capture

Arm the capture with:

```python
dev.spi.capture_start()
```

With triggers configured, RH01T9k waits until a trigger matches before storing records.

Capture stops automatically when a configured limit is reached. Otherwise it can be stopped manually:

```python
status = dev.spi.capture_status()

if status.armed:
    dev.spi.capture_stop()
```

<div class="note"><strong>Note:</strong> Stop the capture, or wait for automatic completion, before reading the records. Reading while capture remains active can produce an inconsistent snapshot.</div>

## Capture records

`capture_records()` returns START, BYTE, and END records.

Each record includes:

* event type
* timestamp
* MOSI byte
* MISO byte
* transaction-loss status

For BYTE records, MOSI and MISO contain the values transferred during the same SPI byte.

The timestamp can be converted to:

```python
record.timestamp.seconds
record.timestamp.milliseconds
record.timestamp.microseconds
record.timestamp.nanoseconds
```

## Capture status

`capture_status()` reports the current capture state.

Important fields include:

| Field               | Meaning                                                              |
| ------------------- | -------------------------------------------------------------------- |
| `armed`             | Capture is waiting for a trigger or actively recording               |
| `triggered`         | Recording has started                                                |
| `done`              | Capture stopped automatically because a configured limit was reached |
| `count`             | Number of stored capture records                                     |
| `transaction_count` | Number of completed captured transactions                            |
| `byte_count`        | Number of captured BYTE events                                       |
| `full`              | All 512 capture records are occupied                                 |
| `loss_or_overflow`  | One or more capture events were lost or the buffer overflowed        |

A manual `capture_stop()` clears `armed` but does not set `done`.

## Capture loss and overflow

SPI operation is not stalled when the capture path cannot accept another event. Instead, SPI continues and capture reports the loss.

If:

```text
loss_or_overflow=True
```

or an END record reports:

```text
lost=True
```

the capture should not be treated as a complete SPI trace.

## Clear capture state

Before starting a new capture, clear the previous records:

```python
dev.spi.capture_clear()
```

To also clear global error flags:

```python
dev.clear_errors()
```

Starting a new capture without clearing first appends records to the existing capture buffer.

## Complete example

Set `PORT` to the serial port assigned to RH01T9k.

```python
from hil import HIL

PORT = "COM7"
BAUD = 115200

with HIL(PORT, BAUD) as dev:
    dev.ping()
    dev.spi.capture_clear()

    dev.spi.capture_configure(
        triggers=[
            (0xFF, 0x60),  # (mask, value)
            (0xFF, 0x85),
            (0xFF, 0xE0),
        ],
        transaction_limit=10,
        record_limit=512,
    )

    dev.spi.capture_start()

    input(
        "Run SPI traffic; capture starts on MOSI command "
        "0x60, 0x85, or 0xE0. Press Enter... "
    )

    status = dev.spi.capture_status()

    if status.armed:
        dev.spi.capture_stop()
        status = dev.spi.capture_status()

    print(status)

    records = dev.spi.capture_records()

    if not records:
        print("No capture records.")
    else:
        origin = records[0].timestamp

        for record in records:
            elapsed = record.timestamp - origin

            print(
                f"{record.index:4d}  {record.type_name:5s}  "
                f"t={elapsed.microseconds:10.3f} us  "
                f"MOSI=0x{record.mosi:02X}  "
                f"MISO=0x{record.miso:02X}  "
                f"lost={record.transaction_lost}"
            )
```
