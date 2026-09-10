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
