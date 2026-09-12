---

layout: layouts/docs.njk
tags: docs
title: Troubleshooting
navExclude: true
---

# Troubleshooting

Start with a simple connection test:

```python
from hil import HIL

with HIL("COM7", 115200, timeout=2.0) as board:
    board.ping()

    status = board.get_status()

    print(f"status = 0x{status.raw:04X}")
    print(status)
```

Read the status before calling `clear_errors()`. Some error flags remain set after the original problem has ended and can help identify what happened.

## Cannot connect to the board

If the serial port does not open or `ping()` times out:

* Confirm that the USB cable supports data.
* Confirm that `PORT` matches the RH01T9k serial port.
* Keep the UART baud rate at `115200`.
* Close serial terminals, IDE monitors, or other programs using the same port.
* Disconnect and reconnect the board if the serial device appears stale.
* Confirm that the Python API and FPGA image are compatible.

The UART control rate is separate from the SPI clock rate.

## Ping succeeds but status reports errors

`ping()` verifies communication but does not clear earlier errors.

Inspect the status first, then clear errors:

```python
status = board.get_status()
print(status)

board.clear_errors()
```

For capture-related errors, also clear the capture buffer:

```python
board.spi.capture_clear()
board.clear_errors()
```

## SPI controller reads incorrect data

Check the following:

* SPI controller and RH01T9k use the same SPI mode.
* SCLK is at or below 20 MHz.
* CS remains low for the complete transaction.
* CS returns high between transactions.
* Read/write masks and address decoding match the controller protocol.
* The controller sends the expected number of dummy bytes.
* `response_delay_bytes` matches the expected response timing.

Use SPI capture to compare the actual MOSI command with the expected command.

A normal zero-delay register read looks like:

```text
MOSI:  COMMAND  DUMMY       DUMMY       ...
MISO:  DEFAULT  REGISTER    REGISTER    ...
```

## Modes 1 or 3 fail on the first byte

SPI Modes 1 and 3 require setup time between CS assertion and the first SCLK edge.

Configure a non-zero CS-to-SCLK delay in the SPI controller. One full SCLK period is a conservative setting.

Also confirm that SCLK is already at the correct idle polarity before CS is asserted.

## SPI becomes unreliable at higher clock rates

If communication works at low speed but becomes unreliable near 20 MHz:

* Reduce SCLK and retest.
* Shorten SPI wiring.
* Use a solid common ground.
* Avoid long solderless-breadboard connections.
* Confirm all signals use compatible 3.3 V logic.
* Verify SPI mode and CS timing.

Increase the SPI clock gradually after basic reads and writes are working reliably.

## Register changes do not appear on the running emulator

`RegisterDevice` is the configuration model used when the emulator is initialized.

Changing the Python object later does not automatically update the running RH01T9k:

```python
registers[0x20] = 0x5A
```

To update the running register image, use operations such as:

```python
board.spi.write_register(...)
board.spi.write_block(...)
board.spi.update_atomic(...)
```

or reload the complete model with:

```python
board.spi.emulate_registers(registers)
```

## Multi-byte values are inconsistent

Related bytes should not be updated independently when the SPI controller may read them during the update.

For a coherent multi-byte value, use an atomic update:

```python
board.spi.configure_atomic_window(0x12, 6)

board.spi.update_atomic(
    0x12,
    six_byte_sample,
)
```

This allows related register bytes to become visible together between SPI transactions.

## Capture does not start

If capture remains armed with no records, the trigger probably did not match the first MOSI byte.

Temporarily capture without a trigger:

```python
board.spi.capture_clear()

board.spi.capture_configure(
    transaction_limit=4,
    record_limit=64,
)

board.spi.capture_start()
```

Inspect the captured MOSI command bytes, then configure the trigger using the observed traffic.

## Capture is full or incomplete

The capture buffer holds a maximum of 512 **records**, not 512 transactions.

Each normal SPI transaction requires:

```text
START + BYTE records + END
```

For an N-byte SPI transaction, this is normally `N + 2` capture records.

If capture reports:

```text
loss_or_overflow=True
```

or a record reports:

```text
lost=True
```

do not treat the capture as complete.

Use a smaller transaction limit or a more selective trigger, then clear the capture before trying again.

## Configuration or capture commands time out

Some operations wait for a safe boundary between SPI transactions.

If the external SPI controller keeps CS low, configuration, register commits, or capture control may not complete.

Check:

```python
status = board.get_status()

print("CS low:", status.spi_cs_low)
print("SPI armed:", status.spi_armed)
```

Make sure the controller returns CS high between transactions before retrying.

## Clean recovery

After correcting the underlying problem:

```python
board.spi.disable()

board.spi.capture_clear()
board.clear_errors()

board.spi.emulate_registers(registers)
```

If communication still fails, stop the external SPI controller, reconnect or reset RH01T9k, then retest at a low SPI clock rate.
