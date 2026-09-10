from hil import HIL

PORT = "COM4"
BAUD = 115200

with HIL(PORT, BAUD) as dev:
    dev.ping()
    dev.spi.capture_clear()
    dev.spi.capture_configure(
    triggers=[
        (0xFF, 0x60),  # exact 0x60
        (0xFF, 0x85),  # exact 0x85
        (0xFF, 0xE0),  # exact 0xE0
    ],
    transaction_limit=10,
    record_limit=512,
)
    dev.spi.capture_start()

    input("Run SPI traffic; capture starts on MOSI command 0x60. Press Enter... ")

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
                f"MOSI=0x{record.mosi:02X}  MISO=0x{record.miso:02X}  "
                f"lost={record.transaction_lost}"
            )
