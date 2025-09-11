## Дослідження по LuckFox

В мене версія без Ethernet. При спробі підключити зовнішній USB-Ethernet адаптер,
зрозумів шо USB-Host відключен.

https://wiki.luckfox.com/Luckfox-Pico/Luckfox-Pico-USB

І треба правити dts шоб його увімкнути, і, напевно
перепрошивати плату.

Пробуємо свою прошивку https://wiki.luckfox.com/Luckfox-Pico/Linux-MacOS-Burn-Image

Дозволити на MacOS виконання утіліти оновлення прошивки.

```
xattr -dr com.apple.quarantine ./upgrade_tool
```


## Пробуємо зібрати SDK

Будемо пробувати на Ubuntu Linux

https://wiki.luckfox.com/Luckfox-Pico/Luckfox-Pico-SDK/


libffi в buildroot відмовився збиратись

Не знаю як краще, вручну пофіксив
sysdrv/source/buildroot/buildroot-2023.02.6/package/libffi/libffi.mk

```
LIBFFI_VERSION = 3.4.6
``

та
sysdrv/source/buildroot/buildroot-2023.02.6/package/libffi/libffi.hash

```
sha256  b0dea9df23c863a7a50e825440f3ebffabd65df1497108e5d437747843895a4e  libffi-3.4.6.tar.gz
```


Можливо це якось можна зробити підсунувши свій `BUILDROOT_VER` у `sysdrv/Makefile`


Хоча ось шо знайшов:

https://github.com/mingzhangqun/luckfox-pico/commit/050175246d74a27ad4edc683c140fc89afa97996


Пробуємо правити dts

<SDK directory>/sysdrv/source/kernel/arch/arm/boot/dts/rv1103g-luckfox-pico-mini-b.dts

Переключаємо USB у HOST-режим

sysdrv/source/kernel/arch/arm/boot/dts/rv1103g-luckfox-pico-mini.dts
```
/**********USB**********/
&usbdrd_dwc3 {
	status = "okay";
	dr_mode = "peripheral";
	dr_mode = "host";
};
```


## Спроба PPM

Я експереметував на LuckFox Pico Mini A/B:

PWM10_1 - Pin 54
PWM11_1 - Pin 55

Але одразу затик:

```
ls -l /sys/class/pwm
```

Показує шо немає нічого
