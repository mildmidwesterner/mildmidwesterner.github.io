---
layout: layouts/docs.njk
tags: docs
navExclude: true
title: SPI Capture Example
downloads:
  - name: 03_capture.py
    url: /assets/downloads/03_capture.py
---

<div class="eyebrow">Example03</div>

# SPI Transaction Capture

This example uses the RH01T9k as an SPI peripheral and records activity from the physical SPI bus. 
The capture can begin immediately or wait for the first MOSI command byte to match user-defined trigger rules. 

Representative output for one SPI transaction is:

```text
   0  start  t=     0.000 us  MOSI=0x00  MISO=0x00  lost=False
   1  byte   t=     1.185 us  MOSI=0x60  MISO=0x00  lost=False
   2  byte   t=     4.889 us  MOSI=0x11  MISO=0x00  lost=False
   3  end    t=     8.630 us  MOSI=0x00  MISO=0x00  lost=False
```

Capture has a physical maximum of 512 records. It is not an unlimited streaming capture.

### Step 1: Configure trigger rules

`spi.capture_configure()` defines the trigger conditions and capture limits used for the recording.

```python

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
```

The example configures three exact-match rules. Capture begins when the first command byte equals `0x60`, `0x85`, or `0xE0`.

Only the first completed MOSI byte after CS goes low is tested. In a register protocol, this is normally the command byte. Trigger rules do not examine later data bytes in the transaction. 

<div class="note"><strong>Caution:</strong>  At most four trigger rules can be configured. Supplying five or more raises an error. </div>

Each trigger is a `(mask, value)` pair. A capture rule matches when:

```text
(first_mosi_byte & mask) == (value & mask)
```

A trigger mask can match a family of commands. This rule matches any command from `0xA0` through `0xAF`:

```python
dev.spi.capture_configure(
    triggers=[(0xF0, 0xA0)],
    record_limit=512,
)
```

For example:

```text
0xA0 & 0xF0 = 0xA0  match
0xA5 & 0xF0 = 0xA0  match
0xAF & 0xF0 = 0xA0  match
0xB0 & 0xF0 = 0xB0  no match
```

`triggers=[]` disables trigger matching:

```python
dev.spi.capture_configure(
    triggers=[],
    record_limit=512,
)
```
In this mode, recording begins immediately after `capture_start()`. 

### Step 2: Select capture limits

The API provides three independent limits: `transaction_limit`, `byte_limit`, and `record_limit`. The first applicable limit to complete stops the capture. 

```python
dev.spi.capture_configure(
    triggers=[],
    transaction_limit=0,
    byte_limit=0,
    record_limit=512,
)
```

`transaction_limit=N` stops after the END of the Nth recorded transaction. `transaction_limit = 0` disables the transaction limit.

`byte_limit=N` stops capture after the transaction containing the Nth recorded byte has completed. `byte_limit = 0` disables the byte limit.

`record_limit=N` stops capture after the Nth stored capture record has completed. This is an immediate hard ceiling. `record_limit` may be from `0` through `512`. A value greater than 512 raises:

```text
ValueError: record_limit cannot exceed the 512-record capture depth
```

Using `record_limit=0` disables the automatic record-count stop, but maximum capture depth of 512 cannot be exceeded.


### Step 3: Start capture

After configuration, arm the capture:

```python
dev.spi.capture_start()
```

With trigger rules, the buffer becomes active and the trigger becomes armed, but no records are stored until a matching first command byte arrives.

`capture_start()` can report a busy error if capture is already active or
armed, the capture buffer is full, or an SPI transaction is currently active. Clear or stop the previous capture and wait for CS to go high before retrying.


### Step 4: Stop capture

Capture stops automatically when it reaches a configured `transaction_limit`, `byte_limit`, or `record_limit`. In that case, `status.done` becomes `True` and no manual stop is needed.

If no automatic limit is configured, or the configured limit has not yet been reached, capture remains armed and continues accepting records. The example checks for that state and stops capture manually:

```python
status = dev.spi.capture_status()
if status.armed:
    dev.spi.capture_stop()
    status = dev.spi.capture_status()
print(status)
```

<div class="note"><strong>Note:</strong> `capture_stop()` stops accepting records but preserves all stored records. A manual stop does not set `status.done`. That field specifically reports an automatic stop caused by a configured limit.</div>

<div class="note"><strong>Caution:</strong> Reading while capture remains active can produce an inconsistent snapshot because new records may be appended after <code>capture_records()</code> reads the count. Stop the capture or wait for <code>status.done</code> before reading records.</div>


## Capture Status

`dev.spi.capture_status()` returns a `CaptureStatus` object with these fields:

| Field | Meaning |
|---|---|
| `active` | The capture buffer is enabled. With triggers, this can be true while waiting for a match. |
| `full` | All 512 physical record entries are occupied. |
| `empty` | No valid records are stored; equivalent to `count == 0`. |
| `loss_or_overflow` | At least one capture event was lost or an event arrived after the buffer was full. See the clearing section below. |
| `count` | Number of valid records currently stored, from 0 through `depth`. |
| `depth` | Physical capture capacity reported by the emulator board; currently 512 records. |
| `armed` | The trigger/capture gate is armed. It remains true while waiting for a trigger and while recording, then clears on stop, clear, or automatic completion. |
| `triggered` | Recording has begun. With triggers, a rule matched; without triggers, it becomes true immediately at start. |
| `done` | An automatic transaction, byte, or record limit stopped the capture. Manual stop does not set it. |
| `transaction_count` | Number of recorded END events, representing completed captured transactions in the current capture run. |
| `byte_count` | Number of recorded BYTE events in the current capture run. START and END are not included. |

`count` and the two counters are related but not interchangeable:

```text
count = BYTE records + START records + END records
byte_count = BYTE records only
transaction_count = completed END records only
```

Always call `capture_clear()` before a new run. Starting again without clearing appends to the existing capture buffer, while the trigger's byte and transaction counters restart from zero. That can make `count` describe several runs while the counters describe only the latest run.


## Capture Record

Each returned `CaptureRecord` has these fields:

| Field | Meaning |
|---|---|
| `index` | Zero-based position in the capture buffer. |
| `event_type` | Numeric event code: 0 = START, 1 = BYTE, 2 = END. |
| `type_name` | Human-readable event name: `"start"`, `"byte"`, `"end"`, or `"unknown"`. |
| `timestamp` | 48-bit capture event timestamp represented by the Python `Timestamp` object. |
| `mosi` | MOSI byte for a BYTE event; zero for START and END. |
| `miso` | MISO byte transmitted during the same BYTE event; zero for START and END. |
| `transaction_lost` | On an END record, indicates that one or more events from that transaction could not be delivered to capture. Normally false on START and BYTE records. |


`03_capture.py` makes the first captured event time zero and prints every later event relative to it:

```python
origin = records[0].timestamp

for record in records:
    elapsed = record.timestamp - origin
    print(elapsed.microseconds)
```

The API provides converted units:

```python
record.timestamp.seconds
record.timestamp.milliseconds
record.timestamp.microseconds
record.timestamp.nanoseconds
```


## Capture loss and overflow

Capture never stalls the live SPI interface. If the capture pipeline or buffer
cannot accept an event, SPI operation continues and the capture reports loss
instead.

`status.loss_or_overflow` combines two internal conditions:

* Capture buffer overflow: another event arrived after all 512 records were
  occupied.
* Event loss: an SPI START, BYTE, or END event could not be delivered through
  the capture pipeline.

If an event is lost during a transaction but its END record is successfully
stored, that END record reports:

```text
record.transaction_lost == True
```

Representative warning signs are:

```text
CaptureStatus(... loss_or_overflow=True, ...)
```

or:

```text
 127  end    t=   492.815 us  MOSI=0x00  MISO=0x00  lost=True
```

When either appears, do not treat the capture as a complete bus trace.


## Clear records and errors

Stored records and capture errors have separate clearing paths.

Clear the capture buffer, trigger state, capture counters, and buffer-overflow
flag with:

```python
dev.spi.capture_clear()
```

Clear global errors, including the capture pipeline's event-loss flag,
with:

```python
dev.clear_errors()
```

Because `status.loss_or_overflow` combines buffer overflow and event loss, use
both operations when preparing a completely clean capture:

```python
status = dev.spi.capture_status()
if status.armed:
    dev.spi.capture_stop()

dev.spi.capture_clear()
dev.clear_errors()

status = dev.spi.capture_status()
print(status)
```

Expected clean status:

```text
CaptureStatus(active=False, full=False, empty=True,
loss_or_overflow=False, count=0, depth=512, armed=False,
triggered=False, done=False, transaction_count=0, byte_count=0)
```

<div class="note"><strong>Caution:</strong> Capture stop and clear requests wait and retry when the emulator board reports that a
physical SPI transaction is busy. If an external controller holds CS low
indefinitely, the operation can eventually time out. </div>
