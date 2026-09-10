---
layout: layouts/docs.njk
tags: docs
title: Troubleshooting
navExclude: true
---

# Troubleshooting

Start troubleshooting with a small, known-good sequence:

```python
from hil import HIL

with HIL("COM7", 115200, timeout=2.0) as board:
    board.ping()
    status = board.get_status()
    print(f"status = 0x{status.raw:04X}")
    print(status)
```

Preserve the first status result before calling `clear_errors()`. Sticky flags often reveal an earlier fault even when a later command succeeds.

### The serial port does not open

Typical symptoms include “access denied,” “port not found,” or a `serial.SerialException` raised while entering the `HIL` context.

Check the following:

- Confirm that the USB cable supports data; some USB cables provide power only.
- Verify the port after connecting the board. Windows COM numbers can change between USB sockets.
- Close serial terminals, IDE monitors, and other Python processes. Normally only one program can own the port.
- On macOS, prefer `/dev/cu.*` for an outgoing connection.
- Disconnect and reconnect the board if the operating system has retained a stale serial device.
- Ensure `pyserial` is installed in the same Python environment used to run the program.

Do not confuse the UART baud rate with the SPI clock rate. The control connection must remain at 115,200 baud; the external SPI controller can run at a separate rate up to 20 MHz.

### `ping()` times out

A timeout means Python did not receive a complete matching response before the configured deadline.

Likely causes and fixes:

- **Wrong port:** identify the port that appears when RedHors01T9k is connected.
- **Wrong baud rate:** use exactly `115200` with the current board image.
- **Charge-only USB cable:** replace it with a known data cable.
- **Board not running the matching image:** install or boot the intended RedHors01T9k build.
- **Stale serial state:** close the program, reconnect or reset the board, and try a new `HIL` context.
- **Timeout too short for a busy operation:** increase `HIL(..., timeout=...)`, but first check whether SPI chip select is stuck low.

`PacketTimeout` identifies a transport-level incomplete packet. A command-layer timeout can surface as `ProtocolError`, particularly while waiting through retries or stale responses.

### Ping succeeds, but status contains old errors

`ping()` verifies the current round trip; it does not erase earlier failures. UART, packet, SPI-decode, and capture-loss flags can remain asserted after the condition has ended.

Read and record the status, correct its likely cause, then clear and retest:

```python
before = board.get_status()
print(f"before clear: 0x{before.raw:04X}")

board.clear_errors()

after = board.get_status()
print(f"after clear:  0x{after.raw:04X}")
```

If `spi_capture_overflow` remains asserted after `clear_errors()`, also call `capture_clear()`. Capture-buffer overflow and general sticky event loss have separate clear paths.

### UART framing, overrun, or CRC errors

For `uart_framing_error`, verify that the host uses 115,200 baud and that the selected port belongs to RedHors01T9k.

For `uart_overrun_error`, stop other software from transmitting to the port. Avoid sharing one `HIL` instance across unsynchronized threads or processes.

For `packet_rx_crc_error` or `PacketCrcError`:

- Check the USB cable and connectors.
- Avoid repeatedly opening the same port from multiple programs.
- Reset the board and reopen the connection to remove stale partial traffic.
- Confirm that the Python package matches the installed board image.

An occasional error points toward link integrity or connection lifecycle. A repeatable error on one command is more likely an API/board-image version mismatch.

### `unsupported_command` or `invalid_command_length` is set

These flags usually indicate that the Python package and installed board image implement different protocol versions. Use the `hil` package from the same RedHors01T9k release as the board image.

They can also result from another program writing arbitrary bytes to the control port. Close serial monitors that send startup strings, line endings, or terminal commands automatically.

### A command raises `FPGAError`

The current API uses the historical exception name `FPGAError` for a command rejected by RedHors01T9k. Inspect its attributes:

```python
from hil import FPGAError

try:
    board.spi.capture_start()
except FPGAError as exc:
    print(f"code=0x{exc.code:02X}, command=0x{exc.command:02X}")
    raise
```

Common board error categories are:

- **Unsupported command:** package and board-image versions do not match.
- **Invalid length:** the command payload does not match the installed implementation.
- **Invalid parameter:** a supplied mode, mask, range, trigger configuration, or capture limit is not accepted.
- **BUSY:** the requested operation cannot run during the current SPI or capture state.

High-level calls automatically retry BUSY where waiting for a chip-select boundary is expected. Persistent BUSY behavior therefore often ends as a timeout instead of reaching application code as `FPGAError`.

### Configuration, commit, or capture control times out

`configure()`, capture start/stop/clear, and pending register publication depend on safe transaction boundaries. If the external controller keeps `CS_N` low, those operations cannot complete normally.

Check:

```python
status = board.get_status()
print("CS low:", status.spi_cs_low)
print("SPI armed:", status.spi_armed)
print("register image ready:", status.spi_shadow_ready)
```

Corrective actions:

1. Stop the external controller or make it deassert `CS_N`.
2. Call `board.spi.disable()` if immediate recovery is required.
3. Correct the controller's CS behavior.
4. Reconfigure, reload, and enable the emulated device again.

Do not solve a permanently asserted chip select merely by increasing the Python timeout. The controller must provide a genuine high interval between transactions.

### `spi_enable_requested` is true but `spi_armed` is false

Enable requests are acknowledged before the SPI interface arms. Arming waits until the response image is ready and physical `CS_N` is high.

If the state persists:

- Confirm that the external controller is not holding chip select low.
- Confirm that no non-waiting commit is still finishing.
- Check `spi_shadow_ready`.
- Disable, ensure CS is high, and enable again.

Do not begin the first external transaction until `spi_armed` is true when deterministic startup order matters.

### The external controller reads the wrong values

Work through these checks in order:

1. Read the same address with `board.spi.read_register(address)` to confirm the active host-visible image.
2. Confirm that staged values were followed by `commit()`.
3. Use `commit(wait=True)`, the default, before immediately verifying host-side readiness.
4. Confirm SPI mode, especially CPOL and CPHA.
5. Confirm that SCLK is no faster than 20 MHz.
6. Confirm the read mask/value and address mask/shift.
7. Confirm the number of dummy bytes implied by `response_delay_bytes`.
8. Capture MOSI and MISO to see the command the controller actually sent.

If `read_register()` shows the expected value but the external controller does not, focus on SPI electrical connections, mode, clock rate, chip-select timing, command decoding, and response delay.

If both show the old value, verify that the update was committed and that Python did not modify only the local `RegisterDevice` after `emulate_registers()`.

### Changing `RegisterDevice` has no effect on a running board

`RegisterDevice` is a local Python model. Operations such as these change only that object:

```python
sensor[0x20] = 0x5A
sensor.load([1, 2, 3], start=0x30)
```

After initial emulation begins, use `write_register()`, `write_block()`, or `update_atomic()` to change the running board. Alternatively, call `emulate_registers(sensor)` again to reload the entire model.

### `spi_command_decode_error` is set

The first MOSI byte matched neither the configured read pattern nor the write pattern.

Check:

- `read_mask` and `read_value`
- `write_mask` and `write_value`
- Whether the controller sends a separate command byte before its address
- Whether the intended address bits overlap direction bits
- Whether SPI mode errors have corrupted the received command

Use capture with no trigger to observe the first command directly:

```python
board.spi.capture_clear()
board.clear_errors()
board.spi.capture_configure(transaction_limit=1, record_limit=32)
board.spi.capture_start()
```

If captured MOSI differs from the controller's intended byte, investigate mode, wiring, clock rate, and chip-select timing before changing masks.

### Reads are shifted by one or more bytes

The first MISO byte is `default_miso` while RedHors01T9k receives the command. Register response begins in the next byte for `response_delay_bytes=0`.

If data appears early or late:

- Count the command transfer and every dummy transfer in the controller driver.
- Confirm `response_delay_bytes` in `RegisterDevice` or `spi.configure()`.
- Remember that the delay is expressed in complete byte periods.
- Use capture to compare the MOSI command/dummy sequence with MISO response bytes.

The usual zero-delay read is conceptually:

```text
MOSI:  COMMAND  DUMMY/DATA  DUMMY/DATA ...
MISO:  DEFAULT  REGISTER    REGISTER   ...
```

### Mode 1 or mode 3 fails on the first bit or first byte

Modes 1 and 3 require non-zero chip-select setup time before the first SCLK edge. A controller that asserts `CS_N` and launches SCLK simultaneously may corrupt the first transfer.

Enable the controller's hardware CS setup delay. When the setting is specified in SCLK cycles, one full period is a conservative choice. Also verify that the clock idles at the polarity required by the selected mode before asserting chip select.

Modes 0 and 2 prepare the first MISO bit while SCLK is idle, but should still use ordinary controller-generated chip-select timing.

### Operation becomes unreliable near 20 MHz

20 MHz is the maximum specified SCLK rate, not a guarantee that every breadboard or jumper-wire arrangement has sufficient signal integrity.

Try the following:

- Reduce SCLK to 1 MHz and retest.
- Shorten SCLK, MOSI, MISO, CS, and ground connections.
- Provide a direct, low-impedance common ground.
- Avoid loose solderless-breadboard paths at high speed.
- Check that all SPI signals are 3.3 V compatible.
- Verify the selected mode and CS timing with a logic analyzer or RedHors01T9k capture.

Increase clock speed gradually only after reads, writes, and captures are consistently correct.

### Multi-byte values appear torn or inconsistent

Do not publish related bytes with separate `write_register()` calls because each call commits independently.

Publish the complete multi-byte value with one call:

```python
board.spi.configure_atomic_window(0x12, 6)
board.spi.update_atomic(0x12, six_byte_sample)
```

If the external controller can also write those addresses, coordinate ownership. A deliberately staged host value for an address takes effect at commit and can supersede a concurrent external update to that same address.

### `update_atomic()` raises `ValueError`

Check that:

- The update is not empty.
- `start` is from `0x00` through `0xFF`.
- The last byte does not extend past `0xFF`.
- Every value is from 0 through 255.
- If validation regions were declared with `configure_atomic_window()`, the entire update fits inside one region.

The regions declared by `configure_atomic_window()` are Python-side guards. Once any region exists on that `SPI` object, updates outside all declared regions are rejected.

### Capture remains armed and records nothing

The configured trigger probably did not match the first MOSI byte of any transaction.

Check:

- Whether the mask/value pair represents the actual on-wire command.
- Whether the target value contains irrelevant bits outside the mask; those bits are ignored, but clearer canonical values make debugging easier.
- Whether the controller is communicating after capture is armed.
- Whether SPI itself is enabled and armed.
- Whether the command is the first byte after CS assertion.

Stop the capture, clear it, and temporarily run without triggers:

```python
if board.spi.capture_status().armed:
    board.spi.capture_stop()

board.spi.capture_clear()
board.spi.capture_configure(transaction_limit=4, record_limit=64)
board.spi.capture_start()
```

Inspect the resulting first MOSI bytes, then construct the trigger from observed traffic.

### `capture_start()` cannot begin

Capture start is rejected as busy when:

- A capture is already active or armed.
- The physical capture buffer is full.
- An external SPI transaction is in progress.

Stop and clear the previous capture, ensure chip select returns high, and start again:

```python
status = board.spi.capture_status()
if status.active or status.armed:
    board.spi.capture_stop()

board.spi.capture_clear()
board.clear_errors()
board.spi.capture_configure(...)
board.spi.capture_start()
```

### Capture is full, incomplete, or reports overflow

The 512-entry capacity counts event records, not transactions. Each complete N-byte transaction normally requires `N + 2` records: START, N BYTE records, and END.

Corrective actions:

- Reduce `transaction_limit` or `byte_limit`.
- Capture shorter transactions.
- Use a selective trigger rather than immediate capture.
- Leave room for START and END records when selecting `record_limit`.
- Retrieve one capture, clear it, and arm the next instead of expecting unlimited streaming.

If `loss_or_overflow` or `transaction_lost` is true, do not silently accept the capture as complete. Clear both capture state and sticky errors before retrying.

### Capture stops without an END record

`record_limit` is a hard ceiling and may stop capture in the middle of a transaction. In contrast, transaction and byte limits finish the current transaction before stopping.

When complete transactions matter:

- Prefer `transaction_limit`.
- Set `record_limit` high enough for the worst-case transaction length.
- Verify that the final expected event is END.
- Check `loss_or_overflow` and `transaction_lost`.

### `done` is false after manually stopping capture

This is expected. `CaptureStatus.done` means an automatic configured limit completed the capture. It is not a generic “not running” flag.

After `capture_stop()`, use `active=False` and `armed=False` to confirm that capture has stopped. Use `done` only to distinguish automatic limit completion.

### Capture retrieval is slow

`capture_records()` first reads status and then performs one serial request per retained record. A full 512-record capture therefore takes much longer to retrieve than the original SPI activity.

This does not indicate lost SPI performance. Capture occurs independently at SPI speed; retrieval happens afterward over the 115,200-baud control link.

For faster inspection during development:

- Use smaller capture limits.
- Read only selected indices with `capture_read(index)`.
- Trigger close to the event of interest.
- Avoid repeatedly downloading an unchanged full buffer.

### Capture timestamps look too large

`record.timestamp` is absolute board uptime in 27 MHz ticks, not elapsed time since capture started. Convert relative to an origin:

```python
records = board.spi.capture_records()

if records:
    origin = records[0].timestamp
    for record in records:
        elapsed = record.timestamp - origin
        print(elapsed.microseconds)
```

Use `.raw_ticks` only when exact counter values are useful. Use the unit properties for display and subtraction for elapsed intervals.

### Timestamp differences appear to go backward or become enormous

Always subtract an earlier timestamp from a later timestamp:

```python
elapsed = later - earlier
```

Subtraction is modulo `2^48` and correctly handles one wrap. Reversing the operands intentionally produces the complementary modulo interval, which is usually a very large duration.

The API cannot infer multiple complete 120.7-day wraps. Sample the counter more frequently than one wrap period for long-running monitoring.

Also remember that timestamp unit properties are floating-point conversions. Use `.ticks` or `.raw_ticks` when exact integer comparison is required.

### A partial final SPI byte is missing from capture

Only complete eight-bit transfers create BYTE records. If `CS_N` rises partway through a byte, the partial byte is discarded. Keep chip select asserted through the final sampling edge and configure the controller for eight-bit words.

### Recommended clean recovery sequence

When the cause has been corrected and a full software-side restart is not necessary, use:

```python
board.spi.disable()
board.spi.capture_clear()
board.clear_errors()

board.spi.emulate_registers(sensor)
```

Then verify:

```python
status = board.get_status()
assert status.spi_enable_requested
assert status.spi_armed
assert status.spi_shadow_ready
assert not status.spi_cs_low
```

If recovery still fails, stop the external SPI controller, reset or power-cycle RedHors01T9k, reopen the serial connection, reload the register model, and retest first at a low SPI clock rate.


## Practical operating checklist

Before a test:

- Use a 3.3 V SPI controller and connect a common ground.
- Keep SCLK at or below 20 MHz.
- Configure the matching SPI mode.
- In modes 1 and 3, provide non-zero CS setup time before the first SCLK edge.
- Keep CS low through the last sampling edge and return it high between transactions.
- Use the fixed 115,200-baud serial control rate.
- Call `ping()`, inspect `get_status()`, and clear old errors as appropriate.
- Load the register image before enabling the external controller's traffic.
- If enable ordering matters, wait for `spi_armed=True`.

For coherent multi-byte updates:

- Stage all related bytes before one commit.
- Use `update_atomic()` for coherent samples.
- Use `configure_atomic_window()` when host-side range checking adds value.
- Coordinate addresses written by both Python and the external SPI controller.

For capture:

- Call both `capture_clear()` and `clear_errors()` for a clean baseline.
- Remember that the limit is 512 event records, including START and END.
- Leave capacity for complete transactions.
- Stop an armed capture manually if its trigger never occurs.
- Check `loss_or_overflow` and each record's `transaction_lost` flag.
- Subtract capture timestamps to obtain relative `Duration` values.