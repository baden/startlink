import socket
import threading
import time
import json

#Пробую і через GPIO
import RPi.GPIO as GPIO
GPIO.setwarnings(True)
GPIO.setmode(GPIO.BCM)      # GPIO.BOARD не спрацювало

# Також спробуємо через gpiozero

# from gpiozero import DigitalOutputDevice, PWMOutputDevice, Device
# from gpiozero.pins.lgpio import LGPIOFactory
# # gpiozero
# # Вказуємо lgpio як основну фабрику пінів для gpiozero
# factory = LGPIOFactory(chip=0)
# # Device.pin_factory = LGPioFactory()
# Device.pin_factory = factory

led_pin = 17
servo_pin = 18

#led = LED(17) # Use the BCM pin number for your LED
# 1. Керування цифровими виходами On/Off
# Припустимо, що у нас світлодіод підключено до GPIO 17
GPIO.setup(led_pin, GPIO.OUT)
# led = DigitalOutputDevice(led_pin)

# 2. Формування PPM (1..2 мсек)
# Для PPM, що зазвичай використовується для сервоприводів, ми використовуємо PWM.
# gpiozero абстрагує це і дозволяє встановити значення від 0 до 1.
# Для сервоприводів, зазвичай, 1 мс відповідає 0,05-0,07, а 2 мс - 0,10-0,12 в залежності від сервоприводу.
# Тут ми будемо емулювати це значеннями duty_cycle.
# Припустимо, сервопривід підключено до GPIO 18
# ШИМ є ще на пінах GPIO12, GPIO13 та GPIO19

GPIO.setup(servo_pin, GPIO.OUT)
servo = GPIO.PWM(servo_pin, 50) # Частота 50 Гц
servo.start(7.5) # Початкове положення (1.5 мс)

# servo = PWMOutputDevice(servo_pin, frequency=50) # Сервоприводи зазвичай працюють на частоті 50 Гц
# servo.value = 0.5

# SERVER_IP = "127.0.0.1"  # IP сервера
SERVER_IP = "s.navi.cc"  # IP сервера
SERVER_PORT = 8766       # Порт UDP-сервера
SEND_INTERVAL = 15       # Інтервал keep-alive (секунд)
PPM_UPDATE_INTERVAL = 0.1 # 20 мс

latest_axes0 = 0.0
axes_lock = threading.Lock()

def listen(sock):
    global latest_axes0
    while True:
        data, addr = sock.recvfrom(4096)
        try:
            packet = json.loads(data.decode())
            axes = packet.get("axes", [])
            if axes:
                #print(f"axes[0]: {axes[0]}")
                with axes_lock:
                    latest_axes0 = axes[0]
            else:
                print("No axes data")
        except Exception as e:
            print(f"Received from server: {data.decode()}")
            print(f"Error parsing packet: {e}")

def ppm_update():
    global latest_axes0
    prev_axes0 = None
    while True:
        with axes_lock:
            axes0 = latest_axes0
        # Оновлюємо тільки якщо зміна axes0 > 0.05
        if prev_axes0 is None or abs(axes0 - prev_axes0) >= 0.05:
            # Значення axes[0] від -1 до 1
            # Перетворюємо це в діапазон 5..10 для сервоприводу
            duty_cycle = 7.5 + axes0 * 2.5  # -1 -> 5, 0 -> 7.5, 1 -> 10
            print(f"Updating servo: axes[0]={axes0}, duty_cycle={duty_cycle}")
            servo.ChangeDutyCycle(duty_cycle)

            # # Перетворюємо в діапазон 0.05..0.10
            # servo_value = 0.05 + (axes0 + 1) * 0.025  # -1 -> 0.05, 0 -> 0.1, 1 -> 0.15
            # print(f"Updating servo: axes[0]={axes0}, servo_value={servo_value}")
            # servo.value = servo_value

            prev_axes0 = axes0
        time.sleep(PPM_UPDATE_INTERVAL)

def keep_alive(sock):
    while True:
        sock.sendto(b"register", (SERVER_IP, SERVER_PORT))
        print("Keep-alive packet sent.")
        time.sleep(SEND_INTERVAL)

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", 0))  # Вибирає випадковий локальний порт

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

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Client stopped.")

if __name__ == "__main__":
    main()