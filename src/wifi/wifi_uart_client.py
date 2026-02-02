import socket
import threading
import signal
import time
import queue

from uart.uart_handler import UARTHandler
import wifi.socket_utils as socket_utils

# SERVER PC IP
SERVER_HOST = "10.249.78.67"
SERVER_PORT = 8000
RECONNECT_INTERVAL = 5


running = True
uart_q = queue.Queue(maxsize=100)
cmd_q = queue.Queue(maxsize=50)
uart = None


def put_latest(q: queue.Queue, item):
    try:
        q.put_nowait(item)
    except queue.Full:
        try:
            q.get_nowait()  # If full, discard last one
            q.put_nowait(item)
        except:
            pass


def receive_uart(uart: UARTHandler):
    global running

    def on_receive(line: str):
        put_latest(uart_q, line)
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
        put_latest(cmd_q, line)

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


def socket_client_loop():
    global running

    conn = None

    while running:
        try:
            print("[Socket] Trying to connect...")
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn.settimeout(3)
            conn.connect((SERVER_HOST, SERVER_PORT))
            conn.settimeout(None)

            print("[Socket] Connected to server")

            t_recv = threading.Thread(
                target=recieve_cmd,
                args=(conn, SERVER_HOST),
                daemon=True
            )
            t_send = threading.Thread(
                target=send_report,
                args=(conn,),
                daemon=True
            )

            t_recv.start()
            t_send.start()

            # 연결 유지 대기
            while running and t_recv.is_alive() and t_send.is_alive():
                time.sleep(0.2)

        except Exception as e:
            print("[Socket] Connection failed:", e)

        finally:
            try:
                if conn is not None: 
                    conn.close()
            except:
                pass

            print("[Socket] Disconnected. Retry in 5s")
            time.sleep(RECONNECT_INTERVAL)


def main():
    global uart

    try:
        uart = UARTHandler(tx=23, rx=24, baud=57600)

        signal.signal(signal.SIGINT, shutdown)
        signal.signal(signal.SIGTERM, shutdown)

        threading.Thread(
            target=receive_uart,
            args=(uart,),
            daemon=True
        ).start()

        threading.Thread(
            target=send_cmd,
            args=(uart,),
            daemon=True
        ).start()

        threading.Thread(
            target=socket_client_loop,
            daemon=True
        ).start()

        while running:
            time.sleep(1)

    finally:
        shutdown()


if __name__ == "__main__":
    main()
