import socket
import threading
import signal

from uart.uart_handler import UARTHandler
import socket_utils

HOST = "0.0.0.0"   # 모든 인터페이스
PORT = 8000

running = True
esp32_history = []
uart = None


def receive_data(uart: UARTHandler):
    global running

    def on_receive(line: str):
        esp32_history.append(line)
        print(f"[ESP32] {line}")

    uart.listen(on_receive, is_running=lambda: running)

    print("[UART receiver stopped]")


def handle_client(conn: socket.socket, addr, uart: UARTHandler):
    global running

    print(f"[PC connected] {addr}")

    def on_receive(line: str):
        print(f"[PC] {line}")
        uart.println(line)

    try:
        socket_utils.listen(conn, on_receive, is_running=lambda: running)
    finally:
        print(f"[PC disconnected] {addr}")
        conn.close()


def shutdown(signum=None, frame=None):
    global running, uart
    print("\n[Shutdown] Cleaning up...")

    running = False

    if uart is not None:
        try:
            uart.destroy()
            print("[Shutdown] UART destroyed")
        except Exception as e:
            print("[Shutdown] UART destroy failed:", e)


def main():
    global uart 
    
    try: 
        uart = UARTHandler(tx=23, rx=24, baud=57600)
        
        signal.signal(signal.SIGINT, shutdown)   # Ctrl+C
        signal.signal(signal.SIGTERM, shutdown)  # systemd / kill

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
            s.settimeout(0.5)
            s.listen()

            print(f"[UART bridge server] listening on {PORT}")

            while running:
                try:
                    conn, addr = s.accept()
                    threading.Thread(
                        target=handle_client,
                        args=(conn, addr, uart),
                        daemon=True
                    ).start()
                except socket.timeout:
                    continue

    except Exception as e:
        print("Server error:", e)

    finally:
        shutdown()


if __name__ == "__main__":
    main()
