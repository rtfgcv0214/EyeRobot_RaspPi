import socket
import threading
import signal
import time
from queue import Queue

from uart.uart_handler import UARTHandler
import wifi.socket_utils as socket_utils

HOST = "0.0.0.0"   # 모든 인터페이스
PORT = 8000

running = True
uart_q = Queue()
cmd_q = Queue()
uart = None


def receive_uart(uart: UARTHandler):
    global running

    def on_receive(line: str):
        uart_q.put(line)
        print("[recieve_uart]: ", line)

    uart.listen(on_receive, is_running=lambda: running)

    print("UART receiver stopped")


def send_report(conn: socket.socket):
    global running, uart_q

    while running:
        try:
            report = uart_q.get(timeout=0.1)
        except:
            continue 

        try: 
            conn.sendall((report + '\n').encode("utf-8"))
        except Exception as e:
            break
            
        print("[send_report]: ", report)
    
    print("Report sender stopped")


def recieve_cmd(conn: socket.socket, addr):
    def on_receive(line: str):
        cmd_q.put(line)

    socket_utils.listen(conn, on_receive, is_running=lambda: running)

    print(f"Client disconnected: {addr}")


def send_cmd(uart: UARTHandler):
    global running, cmd_q

    while running:
        try:
            cmd = cmd_q.get(timeout=0.1)
            print("[send_cmd]: ", cmd)
            uart.println(cmd)
        except:
            pass
    
    print("cmd sender stopped")


def shutdown(signum=None, frame=None):
    global running, uart
    print("\n[Shutdown] Cleaning up...")

    running = False
    time.sleep(0.1)

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
            target=receive_uart,
            args=(uart,),
            daemon=True
        ).start()

        # UART sender thread
        threading.Thread(
            target=send_cmd,
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

                    # command reciever
                    threading.Thread(
                        target=recieve_cmd,
                        args=(conn, addr),
                        daemon=True
                    ).start()
                    
                    # command sender
                    threading.Thread(
                        target=send_report,
                        args=(conn,),
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
