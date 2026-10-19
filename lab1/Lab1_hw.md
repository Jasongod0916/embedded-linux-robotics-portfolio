# **嵌入式系統實驗報告：建置 Raspberry Pi 交叉編譯工具鏈**

## **基本資訊**

**學生姓名： 邱世宇 614530036**

**實驗日期： 2026年3月3日**

## **一、 實驗環境：**

**主機系統： Windows 11 / VirtualBox 7.x**

**開發系統： Ubuntu 22.04 LTS (分配 8GB RAM, 4 CPU, 50GB Disk)**

**目標架構： ARM v6 (Raspberry Pi)**

**工具版本： Binutils 2.40, GCC 12.3.0, Glibc 2.38**

## **二、 實驗目的**

透過原始碼（Source Code）手動建置交叉編譯工具鏈（Cross-Compiler Toolchain）。理解「主機（Host）」與「目標機（Target）」之間的架構差異，並掌握 Sysroot 的建構流程，為後續 Linux 核心編譯與驅動程式開發建立基礎。

## **三、 實作流程與步驟**

### 1. 第一階段：基礎工具建置 (Bare-metal)

Binutils (v1): 建立基礎的組譯器與連結器。

GCC (v1): 編譯「不帶標頭檔」的簡易編譯器，僅用於編譯 Linux 核心與 C 函式庫。

### 2. 系統根目錄 (Sysroot) 準備

Kernel Headers: 安裝 Linux 核心標頭檔，定義硬體通訊介面。

Glibc: 編譯 C 標準函式庫，並安裝至目標目錄 ~/WORK/sysroot。

### 3. 第二階段：終極工具鏈建置 (Final Toolchain)

Binutils (v2): 加入 --with-sysroot 參數重新編譯，使其具備完整的路徑搜尋能力。

GCC (v2): 編譯支援 C++ 且連結 Glibc 的最終版交叉編譯器。

## 三、 遇到的問題與解決方案

在實驗過程中，我遇到了兩個關鍵的編譯錯誤，皆與現代 Linux 發行版的套件異動有關：

### 1. 錯誤：makeinfo: not found (錯誤代碼 127)

問題描述： 在 make install Binutils 時，系統噴出 WARNING: 'makeinfo' is missing 並終止流程。

原因分析： 原始碼編譯過程中預設會產生 .info 格式的說明文件，而 Ubuntu 預設環境未安裝 texinfo 工具。

解決方案： 執行 sudo apt install texinfo -y 補齊套件後重新編譯。

### 2. 錯誤：fatal error: crypt.h: No such file or directory

問題描述： 在編譯 Final GCC 或 Glibc 相關組件時，系統無法找到加密相關的標頭檔。

原因分析： 現代 Ubuntu 版本（如 22.04+）將原本整合在 C 函式庫中的 libcrypt 移除，改為獨立的 libxcrypt。

解決方案： 手動安裝開發用開發庫：sudo apt install libcrypt-dev -y

## 四、 實驗結果驗證

使用建置完成的 crossgcc2 編譯簡單的 hello.c 程式，並透過 file 指令進行檢查：

### 1. 建立一個 hello.c

`cd ~/WORK`

`nano hello.c`

### 2. 輸入內容

```#include <stdio.h>

int main() {

    printf("Hello! This is a cross-compiled program for Raspberry Pi.\n");

    return 0;

}
```

### 3. 編譯

暫時設定環境變數，讓系統找得到你的工具

`export PATH=$PATH:/home/jasonchiu/WORK/crossgcc2/bin`

執行交叉編譯

`arm-linux-gnueabihf-gcc hello.c -o hello_arm `

### 4. 驗證

`file hello_arm`

output： jasonchiu@jasonchiu-VirtualBox:~/WORK$ file hello_arm

hello_arm: ELF 32-bit LSB executable, ARM, EABI5 version 1 (SYSV), dynamically linked, interpreter /lib/ld-linux-armhf.so.3, for GNU/Linux 3.2.0, with debug_info, not stripped

確認產出的執行檔為 ARM 架構，證明交叉編譯環境已完全正確建置。

## 五、 心得感悟

透過這次實驗，我深刻體會到嵌入式開發環境配置的嚴謹性。每一個路徑參數（如 --with-sysroot）都直接影響工具鏈是否能正確定位函式庫。雖然編譯過程漫長且易出錯，但這套從底層建構起來的環境，將為後續的 Linux 核心編譯與驅動程式開發打下紮實的基礎。

## 六、問題

1. --with-sysroot 與 --with-arch 的目的
   --with-sysroot 是用來指定目標系統（target system）的根目錄（root filesystem），讓 cross compiler 在編譯與連結時，能正確使用目標平台的標頭檔（headers）與函式庫（libraries）。這可以避免誤用主機（host）系統的資源，確保產生的執行檔能在目標裝置上正常運作。
   而 --with-arch 則是用來指定目標 CPU 的架構（architecture），例如 armv7、armv8 等，編譯器會依此產生對應指令集的機器碼。這不只是效能優化的選項，更直接決定產生的程式是否能在該硬體上執行。

2. Raspberry Pi 3B+ 是否可設為 --with-arch=armv8
   Raspberry Pi 3B+ 的處理器為 ARM Cortex-A53，屬於 ARMv8 架構，因此從硬體角度來看，確實支援 armv8（64-bit）。然而，是否可以設定為 --with-arch=armv8，取決於所使用的作業系統。若系統為常見的 Raspberry Pi OS（32-bit，armhf），則其使用的是 ARMv7 的執行環境，這時若編譯成 armv8（aarch64）架構的程式，將無法在該系統上執行。因此，只有在使用 64-bit 作業系統（如 aarch64 的 Raspberry Pi OS 或其他 64-bit Linux）時，才適合設定 --with-arch=armv8；否則應設定為 armv7-a 以確保相容性。
