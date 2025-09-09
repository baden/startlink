import socket
import time

SERVER_IP = "127.0.0.1" # Публічна IP-адреса VPS
SERVER_PORT = 12345

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# sock.bind(('0.0.0.0', 12347)) # Можна прив'язати до іншого порту

print("Control Station Client started...")
try:
    while True:
        message = f"CS_status_{time.time()}"
        sock.sendto(message.encode('utf-8'), (SERVER_IP, SERVER_PORT))
        print(f"Sent: {message}")

        sock.settimeout(1.0)
        try:
            data, addr = sock.recvfrom(4096)
            print(f"Received from relay: {data.decode('utf-8')}")
        except socket.timeout:
            pass

        time.sleep(3) # Надсилати трохи рідше, ніж RPi
except KeyboardInterrupt:
    print("\nControl Station Client shutting down.")
finally:
    sock.close()
