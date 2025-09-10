import socket
import threading
import time
import json

#from gpiozero import LED
from gpiozero import DigitalOutputDevice, PWMOutputDevice #, UART

#led = LED(17) # Use the BCM pin number for your LED
# 1. Керування цифровими виходами On/Off
# Припустимо, що у нас світлодіод підключено до GPIO 17
led = DigitalOutputDevice(17)

# 2. Формування PPM (1..2 мсек)
# Для PPM, що зазвичай використовується для сервоприводів, ми використовуємо PWM.
# gpiozero абстрагує це і дозволяє встановити значення від 0 до 1.
# Для сервоприводів, зазвичай, 1 мс відповідає 0,05-0,07, а 2 мс - 0,10-0,12 в залежності від сервоприводу.
# Тут ми будемо емулювати це значеннями duty_cycle.
# Припустимо, сервопривід підключено до GPIO 18
# ШИМ є ще на пінах GPIO12, GPIO13 та GPIO19
servo = PWMOutputDevice(12, frequency=50) # Сервоприводи зазвичай працюють на частоті 50 Гц


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
    while True:
        with axes_lock:
            axes0 = latest_axes0
        # Значення axes[0] від -1 до 1
        # Перетворюємо це в діапазон від 0.05 до 0.10 для сервоприводу
        servo_value = 0.075 + (axes0 * 0.025)
        print(f"axes[0]: {axes0}  servo_value: {servo_value}")
        servo.value = servo_value
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