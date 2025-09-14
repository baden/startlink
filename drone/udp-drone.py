import socket
import threading
import time
import json
from lib_syspwm import HPWM
import subprocess



try:
    import RPi.GPIO as GPIO
    isRPi = True
except ImportError:
    isRPi = False

if isRPi:
    led_pin = 17
    GPIO.setwarnings(True)
    GPIO.setmode(GPIO.BCM)      # GPIO.BOARD не спрацювало
    GPIO.setup(led_pin, GPIO.OUT)
    servo1 = HPWM(0, 1)
    servo2 = HPWM(0, 2)
else:
    # Luckfox Pico Pro
    servo1 = HPWM(5, 0)
    servo2 = HPWM(6, 0)

    from periphery import GPIO
    Buzzer_Pin = 66
    Buzzer_GPIO = GPIO(Buzzer_Pin, "out")
    Buzzer_GPIO.write(False) # LOW

def sound_buzzer(pattern, delay=0.1):
    """
    pattern: list of bools, True=ON, False=OFF
    delay: seconds for each state
    """
    def buzzer_worker():
        for state in pattern:
            Buzzer_GPIO.write(state)
            time.sleep(delay)
        Buzzer_GPIO.write(False)
    threading.Thread(target=buzzer_worker, daemon=True).start()

# Спробую ssd1306
# from SSD1306 import SSD1306
# oled = SSD1306()
# oled.ClearWhite()

from oled.device import ssd1306
from oled.render import canvas
from PIL import ImageFont, ImageDraw, Image
import PIL.ImageOps

device = ssd1306(port=4, address=0x3C)
# font = ImageFont.load_default()
font = ImageFont.truetype(r'fonts/C&C Red Alert [INET].ttf', size=20)


# device.SendCommand(0xb0 + i)
# device.command(0xB0, 0x02, 0x10)
# device.data([0x00,0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x09,0x0A,0x0B,0x0C,0x0D,0x0E,0x0F])

with canvas(device) as draw:
    draw.rectangle((0, 0, device.width, device.height), outline=0, fill=0x00)
    drone_image = Image.open("images/drone.png").convert("1")
    draw.bitmap((0, 0), drone_image, fill=1)
    # draw.text((0, 0), "Init DRONE", font=font, fill=255)


armed_image = Image.open("images/armed.png").convert("1")
armed_image = PIL.ImageOps.invert(armed_image)
disarmed_image = Image.open("images/disarmed.png").convert("1")
disarmed_image = PIL.ImageOps.invert(disarmed_image)

# Також спробуємо через gpiozero

# from gpiozero import DigitalOutputDevice, PWMOutputDevice, Device
# from gpiozero.pins.lgpio import LGPIOFactory
# # # gpiozero
# # # Вказуємо lgpio як основну фабрику пінів для gpiozero
# factory = LGPIOFactory(chip=0)
# # # Device.pin_factory = LGPioFactory()
# Device.pin_factory = factory

# from rpi_hardware_pwm import HardwarePWM

# servo_pin = 18

#led = LED(17) # Use the BCM pin number for your LED
# 1. Керування цифровими виходами On/Off
# Припустимо, що у нас світлодіод підключено до GPIO 17
# led = DigitalOutputDevice(led_pin)

# 2. Формування PPM (1..2 мсек)
# Для PPM, що зазвичай використовується для сервоприводів, ми використовуємо PWM.
# gpiozero абстрагує це і дозволяє встановити значення від 0 до 1.
# Для сервоприводів, зазвичай, 1 мс відповідає 0,05-0,07, а 2 мс - 0,10-0,12 в залежності від сервоприводу.
# Тут ми будемо емулювати це значеннями duty_cycle.
# Припустимо, сервопривід підключено до GPIO 18
# ШИМ є ще на пінах GPIO12, GPIO13 та GPIO19

# GPIO.setup(servo_pin, GPIO.OUT)
# servo = GPIO.PWM(servo_pin, 50) # Частота 50 Гц
# servo.start(7.5) # Початкове положення (1.5 мс)

# Тут це не пін, а канал
# Нам треба /sys/class/pwm/pwmchip0/pwm2
# if not servo.pwmX_exists():
#     servo.create_pwmX()
servo1.set_frequency(50) # 50 Гц
servo1.set_duty_cycle(1.5)
servo1.polarity(normal=True)
servo1.enable()

servo2.set_frequency(50) # 50 Гц
servo2.set_duty_cycle(1.5)
servo2.polarity(normal=True)
servo2.enable()

# servo = HardwarePWM(pwm_channel=1, hz=50, chip=0)
# servo.start(7.5)

# servo = PWMOutputDevice(servo_pin, frequency=50) # Сервоприводи зазвичай працюють на частоті 50 Гц
# servo.value = 0.5

# SERVER_IP = "127.0.0.1"  # IP сервера
SERVER_IP = "s.navi.cc"  # IP сервера
SERVER_PORT = 8766       # Порт UDP-сервера
SEND_INTERVAL = 15       # Інтервал keep-alive (секунд)
PPM_UPDATE_INTERVAL = 0.02 # 20 мс
OLED_UPDATE_INTERVAL = 0.5 # 0.5 секунда

def wait_for_internet(timeout=5):
    while True:
        try:
            # Пінгуємо Google DNS
            subprocess.check_call(["ping", "8.8.8.8", "-c", "1", "-W", str(timeout)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("Інтернет доступний.")
            return
        except subprocess.CalledProcessError:
            print("Немає інтернету. Очікування...")
            time.sleep(2)

latest_axes0 = 0.0
latest_axes1 = 0.0
axes_lock = threading.Lock()

latest_arm_button = False

def listen(sock):
    global latest_axes0, latest_axes1, latest_arm_button
    while True:
        data, addr = sock.recvfrom(4096)
        # print(f"Received from server: {data.decode()}")
        try:
            packet = json.loads(data.decode())
            command = packet.get("command", "")
            if command == "joy_update":
                data = packet.get("data", {})
                axes = data.get("axes", [])
                buttons = data.get("buttons", [])

                if buttons:
                    new_arm_button = buttons[0] == 1
                    if latest_arm_button != new_arm_button:
                        latest_arm_button = new_arm_button
                        if isRPi:
                            GPIO.output(led_pin, GPIO.HIGH if latest_arm_button else GPIO.LOW)
                        else:
                            if latest_arm_button:
                                sound_buzzer([True, False])
                            else:
                                sound_buzzer([True, False, True, False])
                    # print(f"Arm button state: {latest_arm_button}")

                if axes:
                    # print(f"axes[0]: {axes[0]}")
                    # print(f"axes[1]: {axes[1]}")
                    with axes_lock:
                        if latest_arm_button: # Оновлюємо лише якщо дрон заарміний
                            latest_axes0 = axes[0]
                            latest_axes1 = axes[1]
                        else:
                            latest_axes0 = 0.0
                            latest_axes1 = 0.0
                else:
                    print("No axes data", packet)

        except Exception as e:
            print(f"Received from server: {data.decode()}")
            print(f"Error parsing packet: {e}")

def ppm_update():
    global latest_axes0
    global latest_axes1
    prev_axes0 = None
    prev_axes1 = None
    while True:
        with axes_lock:
            axes0 = latest_axes0
            axes1 = latest_axes1
        # Оновлюємо тільки якщо зміна axes0 > 0.05
        if prev_axes0 is None or abs(axes0 - prev_axes0) >= 0.01:
            # # Значення axes[0] від -1 до 1
            # # Перетворюємо це в діапазон 5..10 для сервоприводу
            duty_cycle = 7.5 + axes0 * 2.5  # -1 -> 5, 0 -> 7.5, 1 -> 10
            print(f"Updating servo1: axes[0]={axes0}, duty_cycle={duty_cycle}")
            # servo.ChangeDutyCycle(duty_cycle)
            servo1.set_duty_cycle(1.5 + axes0 * 0.5)  # -1 -> 1.0, 0 -> 1.5, 1 -> 2.0

            # Перетворюємо в діапазон 0.05..0.10
            # servo_value = 0.05 + (axes0 + 1) * 0.025  # -1 -> 0.05, 0 -> 0.1, 1 -> 0.15
            # print(f"Updating servo: axes[0]={axes0}, servo_value={servo_value}")
            # servo.value = servo_value

            # servo.change_duty_cycle(duty_cycle)

            prev_axes0 = axes0

            # with canvas(device) as draw:
            #     draw.rectangle((0, 0, device.width, device.height), outline=0, fill=0)
            #     draw.text((0, 0), f"{axes0}", font=font, fill=255)

        if prev_axes1 is None or abs(axes1 - prev_axes1) >= 0.01:
            duty_cycle = 7.5 + axes1 * 2.5  # -1 -> 5, 0 -> 7.5, 1 -> 10
            print(f"Updating servo2: axes[1]={axes1}, duty_cycle={duty_cycle}")
            servo2.set_duty_cycle(1.5 + axes1 * 0.5)  # -1 -> 1.0, 0 -> 1.5, 1 -> 2.0
            prev_axes1 = axes1
        time.sleep(PPM_UPDATE_INTERVAL)


oled_update_predelay = 5 # Затримка перед першим оновленням OLED 5 cекунд

def oled_update():
    global latest_axes0, latest_axes1, latest_arm_button
    counter = 0
    time.sleep(oled_update_predelay)
    while True:
        with canvas(device) as draw:
            draw.rectangle((0, 0, device.width, device.height), outline=0, fill=0x00)
            draw.text((0, 0), f"{latest_axes0:.2f}:{latest_axes1:.2f}", font=font, fill=255)
            draw.text((0, 14), f"Ping: {counter}", font=font, fill=255)

            if latest_arm_button:
                # draw.bitmap((90, 0), armed_image, fill=1)
                draw.text((90, 0), f"ARM", font=font, fill=255)
            else:
                #draw.bitmap((90, 0), disarmed_image, fill=1)
                draw.text((90, 0), f"DIS", font=font, fill=255)

        counter += 1
        time.sleep(OLED_UPDATE_INTERVAL)

def keep_alive(sock):
    while True:
        sock.sendto(b"register", (SERVER_IP, SERVER_PORT))
        print("Keep-alive packet sent.")
        time.sleep(SEND_INTERVAL)

from crsf import CRSF


def crsf_read(crsf):
    while True:
        crsf.process()
        time.sleep(0.1)


def main():

    # Стартовий піск
    sound_buzzer([True, False])

    crsf = CRSF(port="/dev/ttyS1", baudrate=420000)

    wait_for_internet()
    sock = None

    while True:
        try:
            if sock is None:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.bind(("", 0))
                # Відправляємо перший реєстраційний пакет
                sock.sendto(b"register", (SERVER_IP, SERVER_PORT))
                print("Registration packet sent.")

                # Потік для прослуховування відповідей
                thread_listen = threading.Thread(target=listen, args=(sock,), daemon=True)
                thread_listen.start()

                # Потік для періодичних keep-alive
                thread_keepalive = threading.Thread(target=keep_alive, args=(sock,), daemon=True)
                thread_keepalive.start()

                # Потік для періодичного оновлення PPM
                thread_ppm = threading.Thread(target=ppm_update, daemon=True)
                thread_ppm.start()

                # Потік для оновлення OLED
                thread_oled = threading.Thread(target=oled_update, daemon=True)
                thread_oled.start()

                # Потік для читання з CRSF
                thread_crsf = threading.Thread(target=crsf_read, args=(crsf,))
                thread_crsf.start()

            time.sleep(1)
        except (OSError, socket.error) as e:
            print(f"Втрата зв'язку з сервером: {e}. Перепідключення...")
            if sock:
                try:
                    sock.close()
                except:
                    pass
                sock = None
            wait_for_internet()
        except KeyboardInterrupt:
            print("Client stopped.")
            if sock:
                sock.close()
            break

if __name__ == "__main__":
    main()