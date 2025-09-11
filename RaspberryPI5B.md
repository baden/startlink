# PWM

Довго колупався з PWM

Шо ось зараз (можливо не все треба):


```
dtoverlay=pwm,pin=18,func=2
```

Керування знайшов, беребравши всі варіати, ось тут: /sys/class/pwm/pwmchip0/pwm2

```
cd /sys/class/pwm/pwmchip0
echo 0 > export
cd pwm2
echo 20000000 > period
echo 1000000 > duty_cycle
echo 1 > enable
```

