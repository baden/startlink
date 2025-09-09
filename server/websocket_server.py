import asyncio
# import websockets
from websockets.asyncio.server import serve
import datetime
import json
import logging

# Налаштування логування
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Зберігатимемо активні WebSocket-з'єднання
connected_clients = set()

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
    logging.info(f"WebSocket type: {type(websocket)}")
    logging.info(f"WebSocket methods: {dir(websocket)}")

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
            logging.info(f"Received from {websocket.remote_address}: {message}")

            # Приклад: віддзеркалюємо повідомлення назад клієнту
            # await websocket.send(f"Server received: {message}")

            # Або обробляємо як команду
            try:
                data = json.loads(message)
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
    # Запускаємо фоновий потік для надсилання heartbeat
    heartbeat_task = asyncio.create_task(send_heartbeat())

    # Запускаємо WebSocket-сервер
    # host='0.0.0.0' дозволяє підключення з будь-якої IP-адреси
    # port=8765 - обраний порт
    async with serve(handler, "0.0.0.0", 8765):
        logging.info("WebSocket Server started on ws://0.0.0.0:8765")
        await asyncio.Future() # Запускаємо сервер безкінечно

if __name__ == "__main__":
    asyncio.run(main())
