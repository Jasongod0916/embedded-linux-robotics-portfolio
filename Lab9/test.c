#include <gpiod.h>
#include <stdio.h>
#include <unistd.h>

#define CHIP_NAME "/dev/gpiochip0" // 預設 GPIO 控制器
#define GPIO_LINE 4                // GPIO 4, 對應 pin 7
#define CONSUMER "led"             // 標識用途

int main() {
    struct gpiod_chip *chip;
    struct gpiod_line_settings *line;
    struct gpiod_line_config *line_config;
    struct gpiod_request_config *request_config;
    struct gpiod_line_request *request;
    unsigned int offset = GPIO_LINE;

    // 開啟 gpiochip
    chip = gpiod_chip_open(CHIP_NAME);
    if (!chip) {
        perror("開啟 GPIO chip 失敗");
        return 1;
    }

    // 取得對應 GPIO 腳位
    line = gpiod_line_settings_new();
    if (!line) {
        perror("取得 GPIO line 失敗");
        gpiod_chip_close(chip);
        return 1;
    }

    line_config = gpiod_line_config_new();
    if (!line_config) {
        perror("建立 GPIO line config 失敗");
        gpiod_line_settings_free(line);
        gpiod_chip_close(chip);
        return 1;
    }

    // 設定為輸出，初始值為 0（熄燈）
    gpiod_line_settings_set_direction(line, GPIOD_LINE_DIRECTION_OUTPUT);
    gpiod_line_settings_set_output_value(line, GPIOD_LINE_VALUE_INACTIVE);

    if (gpiod_line_config_add_line_settings(line_config, &offset, 1, line) < 0) {
        perror("設定為輸出失敗");
        gpiod_line_config_free(line_config);
        gpiod_line_settings_free(line);
        gpiod_chip_close(chip);
        return 1;
    }

    request_config = gpiod_request_config_new();
    if (!request_config) {
        perror("建立 request config 失敗");
        gpiod_line_config_free(line_config);
        gpiod_line_settings_free(line);
        gpiod_chip_close(chip);
        return 1;
    }

    gpiod_request_config_set_consumer(request_config, CONSUMER);

    request = gpiod_chip_request_lines(chip, request_config, line_config);
    if (!request) {
        perror("設定為輸出失敗");
        gpiod_request_config_free(request_config);
        gpiod_line_config_free(line_config);
        gpiod_line_settings_free(line);
        gpiod_chip_close(chip);
        return 1;
    }

    // 點燈（設為 1）
    printf("LED ON\n");
    gpiod_line_request_set_value(request, GPIO_LINE, GPIOD_LINE_VALUE_ACTIVE);
    sleep(2);

    // 熄燈（設為 0）
    printf("LED OFF\n");
    gpiod_line_request_set_value(request, GPIO_LINE, GPIOD_LINE_VALUE_INACTIVE);

    // 清理
    gpiod_line_request_release(request);
    gpiod_request_config_free(request_config);
    gpiod_line_config_free(line_config);
    gpiod_line_settings_free(line);
    gpiod_chip_close(chip);

    return 0;
}

// 編譯指令：gcc test.c -o test -lgpiod