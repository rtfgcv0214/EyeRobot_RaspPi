import socket
import threading
from uart.uart_handler import UARTHandler

HOST = "0.0.0.0"   # 모든 인터페이스
PORT = 8000

running = True
esp32_history = []

def receive_data(uart: UARTHandler):
    global running
    buffer = ""

    while running:
        chunk = uart.read(timeout=0.05)
        if not chunk:
            continue

        buffer += chunk

        while '\n' in buffer:
            line, buffer = buffer.split('\n', 1)
            line = line.strip()
            if line:
                esp32_history.append(line)
                print(f"[ESP32] {line}")


def handle_client(conn, addr, uart: UARTHandler):
    print(f"[PC connected] {addr}")
    try:
        with conn:
            buffer = ""
            while running:
                data = conn.recv(1024)
                if not data:
                    break

                buffer += data.decode()

                while '\n' in buffer:
                    cmd, buffer = buffer.split('\n', 1)
                    cmd = cmd.strip()
                    if cmd:
                        print(f"[PC] {cmd}")
                        uart.println(cmd)

    except Exception as e:
        print("Client error:", e)

    print(f"[PC disconnected] {addr}")


def main():
    try:
        uart = UARTHandler(tx=23, rx=24, baud=57600)
    except Exception as e:
        print("UART init failed:", e)
        return

    # UART reciever thread
    threading.Thread(
        target=receive_data,
        args=(uart,),
        daemon=True
    ).start()

    # TCP server
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()

        print(f"[UART bridge server] listening on {PORT}")

        while running:
            conn, addr = s.accept()
            threading.Thread(
                target=handle_client,
                args=(conn, addr, uart),
                daemon=True
            ).start()


if __name__ == "__main__":
    main()
