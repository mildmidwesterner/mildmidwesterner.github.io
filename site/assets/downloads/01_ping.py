from hil import HIL

PORT = "COM7"      # Set assigned serial port 
BAUD = 115200      # Required — do not change


with HIL(PORT, BAUD) as dev:
    dev.ping()
    print("PING OK")

    status = dev.get_status()
    print(f"status = 0x{status.raw:04X}")

