import asyncio
import websockets
from websockets.asyncio.server import serve
import datetime
import json
import logging
import socket

# Налаштування логування
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Зберігатимемо активні WebSocket-з'єднання
connected_clients = set()

# Зберігатимемо адреси UDP-клієнтів
udp_clients = set()

# UDP-сервер: приймає повідомлення та реєструє клієнтів
class UDPServerProtocol:
    def __init__(self):
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport
        logging.info("UDP server started")

    def datagram_received(self, data, addr):
        logging.info(f"UDP packet received from {addr}: {data}")
        # Зараз є два види пакетів:
        # {"command": "register", "id": "ar29wHJT"}
        # {"command": "keep_alive", "id": "ar29wHJT"}
        try:
            json_data = json.loads(data)
            command = json_data.get("command", "")
            id = json_data.get("id", "unknown")
            # І на register і на keep_alive додаємо (або оновлюємо) клієнта. Зберігаємо id.
            udp_clients.add((id, addr))
        except json.JSONDecodeError:
            logging.error(f"Invalid JSON received from {addr}: {data}")
            return  # Зупиняємо обробку, якщо JSON недійсний

        # udp_clients.add(addr)
        # Можна додати обробку вхідних UDP-пакетів тут

    def send_to_clients(self, drone_id: str, message: bytes):
        for id, addr in udp_clients:
            if id == drone_id:
                self.transport.sendto(message, addr)

# Асинхронна функція для надсилання повідомлень кожні 30 секунд
async def send_heartbeat():
    while True:
        await asyncio.sleep(30) # Чекаємо 30 секунд

        message = {
            "type": "heartbeat",
            "timestamp": datetime.datetime.now().isoformat()
        }

        # Перетворимо повідомлення на JSON рядок
        json_message = json.dumps(message)

        # Надішлемо повідомлення всім підключеним клієнтам
        # Одночасно перевіряємо, чи клієнт все ще активний
        # Використовуємо set() для уникнення проблем з модифікацією колекції під час ітерації
        dead_clients = set()
        for websocket in list(connected_clients):
            try:
                await websocket.send(json_message)
                # logging.info(f"Sent heartbeat to {websocket.remote_address}")
            except websockets.exceptions.ConnectionClosed:
                logging.warning(f"Client {websocket.remote_address} disconnected during heartbeat send.")
                dead_clients.add(websocket)
            except Exception as e:
                logging.error(f"Error sending heartbeat to {websocket.remote_address}: {e}")
                dead_clients.add(websocket)

        # Видаляємо неактивних клієнтів
        for client in dead_clients:
            connected_clients.remove(client)

# Основна функція для обробки WebSocket-з'єднань
async def handler(websocket):
    # Show websocket type name and methods
    # logging.info(f"WebSocket type: {type(websocket)}")
    # logging.info(f"WebSocket methods: {dir(websocket)}")

    client_path = "/"
    # client_path = websocket.path
    # 'path' - це шлях, до якого підключився клієнт (наприклад, '/ws' або '/')
    # Для цього прикладу ми його не використовуємо

    logging.info(f"New client connected from {websocket.remote_address} on path {client_path}")

    # Додаємо нового клієнта до списку активних
    connected_clients.add(websocket)

    # Відправляємо вітальне повідомлення одразу після підключення
    welcome_message = {
        "type": "welcome",
        "message": "Welcome to the WebSocket server!",
        "timestamp": datetime.datetime.now().isoformat()
    }
    await websocket.send(json.dumps(welcome_message))

    try:
        async for message in websocket:
            # Логуємо вхідні дані

            # Приклад: віддзеркалюємо повідомлення назад клієнту
            # await websocket.send(f"Server received: {message}")

            # Або обробляємо як команду
            try:
                data = json.loads(message)
                # if data.get("ping", False):
                #     continue

                # logging.info(f"Received from {websocket.remote_address}: {message}")

                # {.."command": "joy_update"..}
                if data.get("command") == "joy_update":
                    if not data.get("ping", False):
                        logging.info(f"Joy update received from {websocket.remote_address}: {message}")
                    payload = data.get("data", {})
                    drone_id = data.get("id", "unknown")
                    # Відправка пакету UDP-клієнтам
                    if udp_server_protocol and udp_server_protocol.transport:
                        udp_server_protocol.send_to_clients(drone_id, json.dumps({"command": "joy_update", "data": payload}).encode())

                if data.get("command") == "restart":
                    logging.info(f"Received restart command from {websocket.remote_address}")
                    # Відправка пакету UDP-клієнтам
                    if udp_server_protocol and udp_server_protocol.transport:
                        udp_server_protocol.send_to_clients(drone_id, json.dumps({"command": "restart"}).encode())
                # # Парсінг пакетів з "axes" та "buttons"
                # if "axes" in data and "buttons" in data:
                #     # Обрізання значень axes до трьох знаків після коми
                #     axes = [round(x, 3) for x in data["axes"]]
                #     buttons = data["buttons"]
                #     logging.info(f"Axes: {axes}")
                #     logging.info(f"Buttons: {[{'pressed': b['pressed'], 'value': b['value']} for b in buttons]}")
                #     # Відправка пакету UDP-клієнтам
                #     udp_message = json.dumps({
                #         "axes": axes,
                #         "buttons": buttons
                #     }).encode()
                #     if udp_server_protocol and udp_server_protocol.transport:
                #         udp_server_protocol.send_to_clients(drone_id, udp_message)
                #     # Відповідь WebSocket-клієнту
                #     await websocket.send(json.dumps({
                #         "type": "parsed",
                #         "axes_count": len(axes),
                #         "buttons_count": len(buttons),
                #         "first_axis": axes[0] if axes else None,
                #         "first_button": buttons[0] if buttons else None,
                #         "axes": axes
                #     }))
                    continue
                if data.get("command") == "get_status":
                    status_response = {
                        "type": "status",
                        "current_time": datetime.datetime.now().isoformat(),
                        "uptime": "simulated_uptime_value",
                        "connected_clients_count": len(connected_clients)
                    }
                    await websocket.send(json.dumps(status_response))
                else:
                    await websocket.send(json.dumps({"type": "error", "message": "Unknown command"}))
            except json.JSONDecodeError:
                logging.warning(f"Received non-JSON message from {websocket.remote_address}: {message}")
                await websocket.send(json.dumps({"type": "error", "message": "Invalid JSON format"}))

    except websockets.exceptions.ConnectionClosed as e:
        logging.info(f"Client {websocket.remote_address} disconnected. Code: {e.code}, Reason: {e.reason}")
    except Exception as e:
        logging.error(f"Error with client {websocket.remote_address}: {e}")
    finally:
        # Видаляємо клієнта зі списку при відключенні
        if websocket in connected_clients:
            connected_clients.remove(websocket)
        logging.info(f"Client {websocket.remote_address} removed from active connections.")

async def main():
    global udp_server_protocol
    # Запускаємо фоновий потік для надсилання heartbeat
    heartbeat_task = asyncio.create_task(send_heartbeat())

    # Запускаємо UDP-сервер
    loop = asyncio.get_running_loop()
    udp_server_protocol = UDPServerProtocol()
    transport, _ = await loop.create_datagram_endpoint(
        lambda: udp_server_protocol,
        local_addr=("0.0.0.0", 8766)
    )
    logging.info("UDP Server started on udp://0.0.0.0:8766")

    # Запускаємо WebSocket-сервер
    async with serve(handler, "0.0.0.0", 8765):
        logging.info("WebSocket Server started on ws://0.0.0.0:8765")
        await asyncio.Future() # Запускаємо сервер безкінечно

if __name__ == "__main__":
    asyncio.run(main())
