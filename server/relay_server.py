import socket
import threading
import time

# --- Конфігурація ---
RELAY_PORT = 12345
BUFFER_SIZE = 4096

# Приклад ідентифікаторів клієнтів.
# В реальному застосунку їх потрібно динамічно реєструвати або автентифікувати.
# Для простоти, ми очікуємо два клієнти: 'client1' і 'client2'
# Ключ - це ідентифікатор клієнта, значення - його (IP, Port)
clients = {}
CLIENT_IDS = ["raspberry_pi", "control_station"]

# Блокування для безпечного доступу до словника clients
clients_lock = threading.Lock()

print(f"UDP Relay Server starting on port {RELAY_PORT}...")

def handle_client_traffic(sock):
    while True:
        try:
            data, addr = sock.recvfrom(BUFFER_SIZE)

            with clients_lock:
                # Визначення, який клієнт надіслав дані
                sender_id = None
                for client_id, client_addr in clients.items():
                    if client_addr == addr:
                        sender_id = client_id
                        break

                if sender_id is None:
                    # Новий клієнт або невідомий. Спробуємо його "зареєструвати"
                    # В реальному світі тут була б автентифікація
                    if "raspberry_pi" not in clients:
                        clients["raspberry_pi"] = addr
                        sender_id = "raspberry_pi"
                        print(f"Registered Raspberry Pi from {addr}")
                    elif "control_station" not in clients and addr != clients.get("raspberry_pi"):
                        clients["control_station"] = addr
                        sender_id = "control_station"
                        print(f"Registered Control Station from {addr}")
                    else:
                        print(f"Received data from unknown address {addr}. Data: {data[:50]}...")
                        continue # Ігноруємо невідомих клієнтів

                # Пересилання даних іншому клієнту
                if sender_id == "raspberry_pi":
                    target_id = "control_station"
                elif sender_id == "control_station":
                    target_id = "raspberry_pi"
                else:
                    # Ця гілка не повинна виконуватись, якщо sender_id коректно визначено
                    continue

                target_addr = clients.get(target_id)

                if target_addr:
                    # print(f"Relaying from {sender_id} ({addr}) to {target_id} ({target_addr}) - {len(data)} bytes")
                    sock.sendto(data, target_addr)
                else:
                    print(f"Target client {target_id} not yet connected.")
                    # Optionally, buffer data until target connects, or just drop (for low-latency UDP usually drop)
        except Exception as e:
            print(f"Error in handle_client_traffic: {e}")
            time.sleep(1)

# Створюємо UDP сокет
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('', RELAY_PORT))

# Запускаємо потік для обробки трафіку
traffic_thread = threading.Thread(target=handle_client_traffic, args=(sock,))
traffic_thread.daemon = True # Дозволяє програмі завершитись, якщо main потік завершиться
traffic_thread.start()

print("Relay server is running. Press Ctrl+C to stop.")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nShutting down relay server.")
finally:
    sock.close()