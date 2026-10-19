#include <gpiod.h>
#include <unistd.h>
#include <stdio.h>
#include <stdint.h>
#include <signal.h>

#define CHIPNAME "/dev/gpiochip0"
#define CLK_PIN 25
#define DIO_PIN 24

#define CLOCK_DELAY 5
#define DEFAULT_BRIGHTNESS 0x88
#define AUTO_MODE 0x40
#define START_ADDR 0xC0
#define CLEAN 0x00

struct gpiod_chip *chip;
struct gpiod_line_request *request;

volatile sig_atomic_t running = 1;

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

void handle_sigint(int sig) {
    running = 0;
}

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

int initialize() {
    chip = gpiod_chip_open(CHIPNAME);
    if (!chip) {
        perror("Open chip failed");
        return -1;
    }

    struct gpiod_line_settings *settings = gpiod_line_settings_new();
    struct gpiod_line_config *line_config = gpiod_line_config_new();
    struct gpiod_request_config *request_config = gpiod_request_config_new();

    if (!settings || !line_config || !request_config) {
        perror("Create gpiod config failed");
        gpiod_chip_close(chip);
        return -1;
    }

    gpiod_line_settings_set_direction(settings, GPIOD_LINE_DIRECTION_OUTPUT);
    gpiod_line_settings_set_output_value(settings, GPIOD_LINE_VALUE_INACTIVE);

    unsigned int offsets[2] = {CLK_PIN, DIO_PIN};

    if (gpiod_line_config_add_line_settings(line_config, offsets, 2, settings) < 0) {
        perror("Add line settings failed");
        gpiod_line_settings_free(settings);
        gpiod_line_config_free(line_config);
        gpiod_request_config_free(request_config);
        gpiod_chip_close(chip);
        return -1;
    }

    gpiod_request_config_set_consumer(request_config, "tm1637_marquee");

    request = gpiod_chip_request_lines(chip, request_config, line_config);
    if (!request) {
        perror("Request lines failed");
        gpiod_line_settings_free(settings);
        gpiod_line_config_free(line_config);
        gpiod_request_config_free(request_config);
        gpiod_chip_close(chip);
        return -1;
    }

    gpiod_line_settings_free(settings);
    gpiod_line_config_free(line_config);
    gpiod_request_config_free(request_config);

    return 0;
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

void displaySegments(uint8_t data[4]) {
    startWrite();
    writeByte(AUTO_MODE);
    stopWrite();

    startWrite();
    writeByte(START_ADDR);
    for (int i = 0; i < 4; i++) {
        writeByte(data[i]);
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

int main(void) {
    signal(SIGINT, handle_sigint);

    if (initialize() < 0) {
        return 1;
    }

    // 跑馬燈內容：前後加空白，讓進場和離場更像跑馬燈
    int text[] = {
        -1, -1, -1, -1,
        6, 1, 4, 5, 3, 0, 0, 3, 6,
        -1, -1, -1, -1
    };

    int len = sizeof(text) / sizeof(text[0]);
    uint8_t display[4];

    printf("Marquee start: 614530036\n");
    printf("Press Ctrl+C to stop.\n");

    while (running) {
        for (int i = 0; i <= len - 4 && running; i++) {
            for (int j = 0; j < 4; j++) {
                int value = text[i + j];

                if (value == -1) {
                    display[j] = CLEAN;
                } else {
                    display[j] = segment_map[value];
                }
            }

            displaySegments(display);
            usleep(300000); // 0.3 秒換一次畫面
        }
    }

    end();
    printf("Marquee stop.\n");

    return 0;
}
