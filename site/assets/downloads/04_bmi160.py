"""
BMI160 SPI emulator - scripted motion demo.

The ESP32 firmware remains unchanged.

The FPGA emulates a BMI160 and produces a deterministic
motion sequence:

    flat
      ->
    45 degree tilt
      ->
    90 degree tilt
      ->
    hold
      ->
    return flat

The ESP32 reads the synthetic accelerometer values over SPI
and displays them on the OLED.

Accelerometer XYZ updates are committed atomically so the
ESP32 never sees a partially updated sample.
"""

import math
import time

from hil import HIL, RegisterDevice


# ============================================================
# Connection
# ============================================================

PORT = "COM7"
BAUD = 115200


# ============================================================
# BMI160 registers
# ============================================================

REG_CHIP_ID = 0x00
REG_PMU_STATUS = 0x03

REG_ACC_X_L = 0x12
REG_ACC_X_H = 0x13
REG_ACC_Y_L = 0x14
REG_ACC_Y_H = 0x15
REG_ACC_Z_L = 0x16
REG_ACC_Z_H = 0x17

REG_ACC_CONF = 0x40
REG_ACC_RANGE = 0x41
REG_CMD = 0x7E


# ============================================================
# BMI160 constants
# ============================================================

BMI160_CHIP_ID = 0xD1

PMU_STATUS_ACC_NORMAL = 0x10

ACC_CONF_100HZ = 0x28
ACC_RANGE_2G = 0x03

LSB_PER_G = 16384


# ============================================================
# Atomic window
# ============================================================

ACC_ATOMIC_START = REG_ACC_X_L
ACC_ATOMIC_LENGTH = 6


# ============================================================
# Motion configuration
# ============================================================

UPDATE_MS = 50

FLAT_HOLD_MS = 1000
TILT_TIME_MS = 1500
ANGLE_HOLD_MS = 1000
RETURN_TIME_MS = 1500


# ============================================================
# Conversion helpers
# ============================================================

def clamp_int16(value: int) -> int:
    return max(
        -32768,
        min(32767, int(value)),
    )


def g_to_raw(g_value: float) -> int:
    return clamp_int16(
        round(g_value * LSB_PER_G)
    )


def int16_to_le(value: int) -> tuple[int, int]:

    value = clamp_int16(value)

    if value < 0:
        value += 0x10000

    return (
        value & 0xFF,
        (value >> 8) & 0xFF,
    )


# ============================================================
# Accelerometer register update
# ============================================================

def set_accel(
    dev: HIL,
    x_g: float,
    y_g: float,
    z_g: float,
):

    raw_x = g_to_raw(x_g)
    raw_y = g_to_raw(y_g)
    raw_z = g_to_raw(z_g)

    x_l, x_h = int16_to_le(raw_x)
    y_l, y_h = int16_to_le(raw_y)
    z_l, z_h = int16_to_le(raw_z)

    sample = [
        x_l,
        x_h,
        y_l,
        y_h,
        z_l,
        z_h,
    ]

    # Stage all six accelerometer registers, then commit them
    # together between SPI transactions.
    dev.spi.update_atomic(
        ACC_ATOMIC_START,
        sample,
    )


# ============================================================
# Motion model
# ============================================================

def set_tilt_angle(
    dev: HIL,
    angle_deg: float,
):
    """
    Simulate rotating the sensor around Y.

    0 degrees:
        X = 0
        Z = -1 g

    90 degrees:
        X = +1 g
        Z = 0
    """

    angle_rad = math.radians(angle_deg)

    x_g = math.sin(angle_rad)
    y_g = 0.0
    z_g = -math.cos(angle_rad)

    set_accel(
        dev,
        x_g,
        y_g,
        z_g,
    )

    print(
        f"angle={angle_deg:6.1f} deg   "
        f"X={x_g:+.3f} g   "
        f"Y={y_g:+.3f} g   "
        f"Z={z_g:+.3f} g"
    )


def hold_angle(
    dev: HIL,
    angle_deg: float,
    duration_ms: int,
):

    steps = max(
        1,
        duration_ms // UPDATE_MS,
    )

    for _ in range(steps):

        set_tilt_angle(
            dev,
            angle_deg,
        )

        time.sleep(
            UPDATE_MS / 1000
        )


def move_angle(
    dev: HIL,
    start_deg: float,
    end_deg: float,
    duration_ms: int,
):

    steps = max(
        1,
        duration_ms // UPDATE_MS,
    )

    for step in range(steps + 1):

        fraction = step / steps

        angle_deg = (
            start_deg
            + (end_deg - start_deg)
            * fraction
        )

        set_tilt_angle(
            dev,
            angle_deg,
        )

        time.sleep(
            UPDATE_MS / 1000
        )


# ============================================================
# BMI160 register model
# ============================================================

bmi160 = RegisterDevice(
    mode=0,
    default_miso=0x00,

    # bit 7 = read/write
    read_mask=0x80,
    read_value=0x80,

    write_mask=0x80,
    write_value=0x00,

    # 7-bit BMI160 register address
    address_mask=0x7F,
    address_shift=0,

    # Auto increment during reads.
    auto_increment_mask=0x80,
    auto_increment_value=0x80,

    response_delay_bytes=0,
)


# ============================================================
# Initial register values
# ============================================================

bmi160[REG_CHIP_ID] = BMI160_CHIP_ID
bmi160[REG_PMU_STATUS] = PMU_STATUS_ACC_NORMAL

bmi160[REG_ACC_CONF] = ACC_CONF_100HZ
bmi160[REG_ACC_RANGE] = ACC_RANGE_2G

bmi160[REG_CMD] = 0x00


# Start flat:
#
# X = 0
# Y = 0
# Z = -1 g
bmi160.load(
    [
        0x00, 0x00,
        0x00, 0x00,
        0x00, 0xC0,
    ],
    start=REG_ACC_X_L,
)


# ============================================================
# Run emulator
# ============================================================

with HIL(PORT, BAUD) as dev:

    dev.ping()
    dev.clear_errors()

    print()
    print("Loading BMI160 FPGA emulator...")

    # Load initial register image first.
    dev.spi.emulate_registers(
        bmi160
    )

    # Then define the six accelerometer registers as one
    # coherent atomic-update window.
    dev.spi.configure_atomic_window(
        ACC_ATOMIC_START,
        ACC_ATOMIC_LENGTH,
    )

    print("BMI160 emulator ready")
    print(
        f"Atomic accel window: "
        f"0x{ACC_ATOMIC_START:02X}.."
        f"0x{ACC_ATOMIC_START + ACC_ATOMIC_LENGTH - 1:02X}"
    )
    print("ESP32 firmware remains unchanged")
    print()

    try:

        while True:

            # ------------------------------------------------
            # 1. Flat
            # ------------------------------------------------

            print()
            print("=== FLAT ===")

            hold_angle(
                dev,
                angle_deg=0,
                duration_ms=FLAT_HOLD_MS,
            )


            # ------------------------------------------------
            # 2. Slowly tilt to 45 degrees
            # ------------------------------------------------

            print()
            print("=== TILT TO 45 DEG ===")

            move_angle(
                dev,
                start_deg=0,
                end_deg=45,
                duration_ms=TILT_TIME_MS,
            )


            # ------------------------------------------------
            # 3. Hold 45 degrees
            # ------------------------------------------------

            print()
            print("=== HOLD 45 DEG ===")

            hold_angle(
                dev,
                angle_deg=45,
                duration_ms=ANGLE_HOLD_MS,
            )


            # ------------------------------------------------
            # 4. Tilt to 90 degrees
            # ------------------------------------------------

            print()
            print("=== TILT TO 90 DEG ===")

            move_angle(
                dev,
                start_deg=45,
                end_deg=90,
                duration_ms=TILT_TIME_MS,
            )


            # ------------------------------------------------
            # 5. Hold sideways
            # ------------------------------------------------

            print()
            print("=== HOLD 90 DEG ===")

            hold_angle(
                dev,
                angle_deg=90,
                duration_ms=ANGLE_HOLD_MS,
            )


            # ------------------------------------------------
            # 6. Return to flat
            # ------------------------------------------------

            print()
            print("=== RETURN TO FLAT ===")

            move_angle(
                dev,
                start_deg=90,
                end_deg=0,
                duration_ms=RETURN_TIME_MS,
            )


    except KeyboardInterrupt:

        print()
        print("BMI160 emulator stopped")