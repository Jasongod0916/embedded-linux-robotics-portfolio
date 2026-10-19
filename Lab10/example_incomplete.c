#include <gpiod.h>
#include <unistd.h>
#include <stdio.h>
#include <stdint.h>

#define CHIPNAME "/dev/gpiochip0"
#define CLK_PIN 25
#define DIO_PIN 24

#define CLOCK_DELAY 5
#define DEFAULT_BRIGHTNESS 0x88
// 一次四位
#define AUTO_MODE 0x40
#define FIXED_MODE 0x44
#define START_ADDR 0xC0
#define CLEAN 0x00

struct gpiod_chip *chip;
struct gpiod_line *clk_line;
struct gpiod_line *dio_line;

// 七段顯示的數字對應表
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
    // write the value to the DIO line
    ...
    
    // 確認讀取到正確的值
    delay_us(CLOCK_DELAY);
}


void writeCLK(int value) {
    // write the value to the CLK line
    ...

    // 確認讀取到正確的值
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
    // 忽略ACK
    writeCLK(0);
    writeCLK(1);
    writeCLK(0);
}


void initialize() {
    /*Setup GPIO device*/
    chip = gpiod_chip_open(CHIPNAME);
    if (!chip) {
        perror("Open chip failed");
        return;
    }
    // get chip lines
    ...

    // setup clk_line and dio_line to output mode
    ...
}


// 釋放資源, 關閉七段顯示器
void end() {
    ...
}


// 顯示一個四位數的數字
void showNum(int num) {
    int digits[4] = {0};

    // 把整數拆成個位、十位、百位、千位
    for (int i = 3; i >= 0; i--) {
        digits[i] = num % 10;
        num /= 10;
    }

    // 設定寫入模式：自動加位址
    startWrite();
    writeByte(AUTO_MODE); // 設定自動加位址
    stopWrite();

    // 設定寫入起始位址 0xC0
    startWrite();
    writeByte(START_ADDR); // 位址0開始
    for (int i = 0; i < 4; i++) {
        writeByte(segment_map[digits[i]]);
    }
    stopWrite();

    // 設定亮度最大 & 顯示開啟
    startWrite();
    writeByte(DEFAULT_BRIGHTNESS | 0x07); // 顯示開啟 + 最高亮度
    stopWrite();
}


void showOneDigit(int pos, int num) {
    if (pos < 0 || pos > 3 || num < 0 || num > 9) {
        printf("Invalid position or number\n");
        return;
    }

    // Step1: 選擇 Fixed Address Mode
    startWrite();
    writeByte(FIXED_MODE); // 固定位址模式
    stopWrite();

    // Step2: 指定要寫的位址
    startWrite();
    writeByte(START_ADDR + pos); // 0xC0是第0位，依pos調整
    writeByte(segment_map[num]); // 寫入對應的七段碼
    stopWrite();

    // Step3: 保持顯示器開啟 & 亮度最大
    startWrite();
    writeByte(DEFAULT_BRIGHTNESS | 0x07); // 顯示開啟+最高亮度
    stopWrite();
}


// 清空顯示器
void clearDisplay() {
    // deliver all 0x00 to the display
    ...
}


int main(void) {
    initialize();

    ...

    // 最後清空
    clearDisplay();

    end();
    return 0;
}
