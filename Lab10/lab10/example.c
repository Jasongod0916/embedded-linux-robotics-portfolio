#include <gpiod.h>
#include <unistd.h>
#include <stdio.h>
#include <stdint.h>

#define CHIPNAME "/dev/gpiochip0"
#define CLK_PIN 25
#define DIO_PIN 24

#define CLOCK_DELAY 5
#define DEFAULT_BRIGHTNESS 0x88
#define AUTO_MODE 0x40
#define FIXED_MODE 0x44
#define START_ADDR 0xC0
#define CLEAN 0x00

struct gpiod_chip *chip;
struct gpiod_line_request *request;

const uint8_t segment_map[] = {
    0x3F, // 0
    0x06, // 1
    0x5B, // 2
    0x4F, // 3
    0x66, // 4
    0x6D, // 5
    0x7D, // 6
    0x07, // 7
    0x7F, // 8
    0x6F  // 9
};

void delay_us(int us) {
    usleep(us);
}

void writeDIO(int value) {
    gpiod_line_request_set_value(
        request,
        DIO_PIN,
        value ? GPIOD_LINE_VALUE_ACTIVE : GPIOD_LINE_VALUE_INACTIVE
    );

    delay_us(CLOCK_DELAY);
}

void writeCLK(int value) {
    gpiod_line_request_set_value(
        request,
        CLK_PIN,
        value ? GPIOD_LINE_VALUE_ACTIVE : GPIOD_LINE_VALUE_INACTIVE
    );

    delay_us(CLOCK_DELAY);
}

void startWrite() {
    writeDIO(1);
    writeCLK(1);
    writeDIO(0);
    writeCLK(0);
}

void stopWrite() {
    writeCLK(0);
    writeDIO(0);
    writeCLK(1);
    writeDIO(1);
}

void writeByte(uint8_t byte) {
    for (int i = 0; i < 8; i++) {
        writeCLK(0);
        writeDIO(byte & 0x01);
        writeCLK(1);
        byte >>= 1;
    }

    // 忽略 ACK
    writeCLK(0);
    writeCLK(1);
    writeCLK(0);
}

void initialize() {
    chip = gpiod_chip_open(CHIPNAME);
    if (!chip) {
        perror("Open chip failed");
        return;
    }

    struct gpiod_line_settings *settings;
    struct gpiod_line_config *line_config;
    struct gpiod_request_config *request_config;

    settings = gpiod_line_settings_new();
    line_config = gpiod_line_config_new();
    request_config = gpiod_request_config_new();

    if (!settings || !line_config || !request_config) {
        perror("Create gpiod config failed");
        return;
    }

    gpiod_line_settings_set_direction(settings, GPIOD_LINE_DIRECTION_OUTPUT);
    gpiod_line_settings_set_output_value(settings, GPIOD_LINE_VALUE_INACTIVE);

    unsigned int offsets[2] = {CLK_PIN, DIO_PIN};

    if (gpiod_line_config_add_line_settings(line_config, offsets, 2, settings) < 0) {
        perror("Add line settings failed");
        return;
    }

    gpiod_request_config_set_consumer(request_config, "tm1637");

    request = gpiod_chip_request_lines(chip, request_config, line_config);
    if (!request) {
        perror("Request lines failed");
        return;
    }

    gpiod_line_settings_free(settings);
    gpiod_line_config_free(line_config);
    gpiod_request_config_free(request_config);
}

void clearDisplay() {
    startWrite();
    writeByte(AUTO_MODE);
    stopWrite();

    startWrite();
    writeByte(START_ADDR);

    for (int i = 0; i < 4; i++) {
        writeByte(CLEAN);
    }

    stopWrite();

    startWrite();
    writeByte(DEFAULT_BRIGHTNESS | 0x07);
    stopWrite();
}

void end() {
    clearDisplay();

    if (request) {
        gpiod_line_request_release(request);
    }

    if (chip) {
        gpiod_chip_close(chip);
    }
}

void showNum(int num) {
    int digits[4] = {0};

    if (num < 0) {
        num = 0;
    }

    if (num > 9999) {
        num = 9999;
    }

    for (int i = 3; i >= 0; i--) {
        digits[i] = num % 10;
        num /= 10;
    }

    startWrite();
    writeByte(AUTO_MODE);
    stopWrite();

    startWrite();
    writeByte(START_ADDR);

    for (int i = 0; i < 4; i++) {
        writeByte(segment_map[digits[i]]);
    }

    stopWrite();

    startWrite();
    writeByte(DEFAULT_BRIGHTNESS | 0x07);
    stopWrite();
}

void showOneDigit(int pos, int num) {
    if (pos < 0 || pos > 3 || num < 0 || num > 9) {
        printf("Invalid position or number\n");
        return;
    }

    startWrite();
    writeByte(FIXED_MODE);
    stopWrite();

    startWrite();
    writeByte(START_ADDR + pos);
    writeByte(segment_map[num]);
    stopWrite();

    startWrite();
    writeByte(DEFAULT_BRIGHTNESS | 0x07);
    stopWrite();
}

int main(void) {
    initialize();

    // 基本要求：1000, 0900, 0800, ... , 0000
    for (int i = 1000; i >= 0; i -= 100) {
        printf("Show: %04d\n", i);
        showNum(i);
        sleep(1);
    }

    clearDisplay();
    end();

    return 0;
}