/*
 * generic_spi_master.c
 *
 * ESP32-S3 generic SPI master test driver.
 *
 * Sends SPI transactions from tests[] and prints:
 *   - MOSI bytes sent
 *   - MISO bytes received
 *
 * Pins:
 *   SCLK = GPIO 7
 *   MISO = GPIO 8
 *   MOSI = GPIO 9
 *   CS   = GPIO 4
 */

#include <stdint.h>
#include <stddef.h>
#include <stdio.h>

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include "driver/spi_master.h"

#include "esp_err.h"
#include "esp_rom_sys.h"


// ============================================================
// ESP32-S3 SPI PINS
// ============================================================

#define PIN_NUM_SCLK   7
#define PIN_NUM_MISO   8
#define PIN_NUM_MOSI   9
#define PIN_NUM_CS     4

#define SPI_HOST_USED  SPI2_HOST


// ============================================================
// USER CONFIG
// ============================================================

#define SPI_HZ         1000000
#define SPI_MODE       0   // Must match emulator SPI mode

#define MAX_TEST_BYTES 64


// ============================================================
// TRANSACTION DEFINITION
// ============================================================

typedef struct
{
    uint8_t tx[MAX_TEST_BYTES];
    size_t len;
    uint32_t delay_us;

} spi_test_t;


// ============================================================
// SPI TRANSACTIONS
// ============================================================

static const spi_test_t tests[] =
{
    // Single read: register 0x05
    {
        {0x85, 0x00},
        2,
        1000
    },

    // Single write: register 0x05 = 0x77
    {
        {0x05, 0x77},
        2,
        1000
    },

    // Read back register 0x05
    {
        {0x85, 0x00},
        2,
        1000
    },

    // Burst read: registers 0x20..0x23
    {
        {0xE0, 0x00, 0x00, 0x00, 0x00},
        5,
        1000
    },

    // Burst write: registers 0x20..0x23
    {
        {0x60, 0x11, 0x22, 0x33, 0x44},
        5,
        1000
    },

    // Read back registers 0x20..0x23
    {
        {0xE0, 0x00, 0x00, 0x00, 0x00},
        5,
        1000
    },

    // Repeated write to register 0x20 without auto-increment
    {
        {0x20, 0x11, 0x22, 0x33, 0x44},
        5,
        1000
    },

    // Repeated read of register 0x20 without auto-increment
    {
        {0xA0, 0x00, 0x00, 0x00, 0x00},
        5,
        1000
    },
};


#define NUM_TESTS (sizeof(tests) / sizeof(tests[0]))


static spi_device_handle_t spi;


// ============================================================
// MICROSECOND DELAY
// ============================================================

static void delay_us(uint32_t us)
{
    if (us > 0)
    {
        esp_rom_delay_us(us);
    }
}


// ============================================================
// PRINT BYTE BUFFER
// ============================================================

static void print_bytes(
    const char *label,
    const uint8_t *data,
    size_t len
)
{
    printf("%s", label);

    for (size_t i = 0; i < len; i++)
    {
        printf("%02X ", data[i]);
    }

    printf("\n");
}


// ============================================================
// SEND ONE SPI TRANSACTION
// ============================================================

static void send_transaction(
    const uint8_t *tx_data,
    size_t len
)
{
    if (len == 0 || len > MAX_TEST_BYTES)
    {
        return;
    }

    uint8_t rx_data[MAX_TEST_BYTES] = {0};

    spi_transaction_t t = {0};

    t.length = len * 8;
    t.tx_buffer = tx_data;
    t.rx_buffer = rx_data;

    ESP_ERROR_CHECK(
        spi_device_polling_transmit(spi, &t)
    );

    print_bytes("MOSI: ", tx_data, len);
    print_bytes("MISO: ", rx_data, len);

    printf("\n");
}


// ============================================================
// SPI INITIALIZATION
// ============================================================

static void init_spi(void)
{
    spi_bus_config_t bus_cfg =
    {
        .mosi_io_num = PIN_NUM_MOSI,
        .miso_io_num = PIN_NUM_MISO,
        .sclk_io_num = PIN_NUM_SCLK,

        .quadwp_io_num = -1,
        .quadhd_io_num = -1,

        .max_transfer_sz = MAX_TEST_BYTES
    };


    spi_device_interface_config_t dev_cfg =
    {
        .clock_speed_hz = SPI_HZ,
        .mode = SPI_MODE,
        .spics_io_num = PIN_NUM_CS,
        .queue_size = 1,

        /*
         * Add setup time between CS assertion
         * and the first SPI clock.
         */
        .cs_ena_pretrans = 2,

        /*
         * Hold CS briefly after the final
         * SPI clock edge.
         */
        .cs_ena_posttrans = 2,
    };


    ESP_ERROR_CHECK(
        spi_bus_initialize(
            SPI_HOST_USED,
            &bus_cfg,
            SPI_DMA_CH_AUTO
        )
    );


    ESP_ERROR_CHECK(
        spi_bus_add_device(
            SPI_HOST_USED,
            &dev_cfg,
            &spi
        )
    );
}


// ============================================================
// MAIN
// ============================================================

void app_main(void)
{
    init_spi();

    printf("\nSPI register test started\n\n");

    while (1)
    {
        for (size_t i = 0; i < NUM_TESTS; i++)
        {
            printf("Transaction %u\n", (unsigned)(i + 1));

            send_transaction(
                tests[i].tx,
                tests[i].len
            );

            delay_us(
                tests[i].delay_us
            );
        }

        printf("-----------------------------\n\n");

        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}