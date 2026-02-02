import socket
import threading
import curses
import time

import wifi.socket_utils as socket_utils


PORT = 8000

MOVEMENT_STEP = 0.02
DRAW_INTERVAL = 0.1

running = True

esp32_history = []
cmd_history = []

key = None
azimuth = 0.0
elevation = 0.0

left_win: curses.window | None = None
right_win: curses.window | None = None


def init_ui(stdscr: curses.window):
    global left_win, right_win

    curses.curs_set(0)
    stdscr.nodelay(True)

    height, width = stdscr.getmaxyx()
    mid = width // 2

    left_win = curses.newwin(height, mid, 0, 0)
    right_win = curses.newwin(height, width - mid, 0, mid)

    right_win.timeout(10)
    right_win.keypad(True)


def draw():
    global left_win, right_win
    global esp32_history, cmd_history
    global key, azimuth, elevation

    if left_win is None or right_win is None:
        return

    left_win.clear()
    h, w = left_win.getmaxyx()
    left_win.box()

    instructions = [
        "W/S: Increase/Decrease Elevation",
        "A/D: Decrease/Increase Azimuth",
        "Z: Zero Azimuth/Elevation",
        "Space: Enable/Disable Motors",
        "R: Reboot ESP32",
        "Q: Quit",
    ]

    i = 0
    for line in instructions:
        left_win.addstr(i + 1, 1, line[: w - 2])
        i += 1

    rem = h - 6 - i
    for line in cmd_history[-rem:]:
        left_win.addstr(i + 1, 1, line[: w - 2])
        i += 1

    left_win.addstr(h - 3, 1, f"Azimuth: {azimuth:.2f} Elevation: {elevation:.2f}")
    left_win.addstr(h - 2, 1, "Key: " + (key or "None"))
    left_win.refresh()

    right_win.clear()
    h, w = right_win.getmaxyx()
    right_win.box()

    for i, line in enumerate(esp32_history[-(h - 2):]):
        right_win.addstr(i + 1, 1, line[: w - 2])

    right_win.addstr(0, 2, "ESP32 STATUS")
    right_win.refresh()


def receive_data(conn: socket.socket):
    global running, esp32_history

    def on_receive(line: str):
        esp32_history.append(line)

    socket_utils.listen(
        conn,
        on_receive,
        is_running=lambda: running
    )


def command_loop(conn: socket.socket):
    global running, key
    global azimuth, elevation
    global right_win

    if not right_win:
        return

    motor_enabled = False
    last_draw = time.time()

    while running:
        ch = right_win.getch()
        cmd = None

        if ch == -1:
            key = None
        else:
            key = curses.keyname(ch).decode("utf-8").lower()

        if key == 'w':
            elevation += MOVEMENT_STEP
            cmd = f"2a{elevation:.2f}"
        elif key == 's':
            elevation -= MOVEMENT_STEP
            cmd = f"2a{elevation:.2f}"
        elif key == 'a':
            azimuth -= MOVEMENT_STEP
            cmd = f"1a{azimuth:.2f}"
        elif key == 'd':
            azimuth += MOVEMENT_STEP
            cmd = f"1a{azimuth:.2f}"
        elif key == 'z':
            azimuth = elevation = 0.0
            cmd = "zero"
        elif key == ' ':
            motor_enabled = not motor_enabled
            cmd = "enable" if motor_enabled else "disable"
        elif key == 'r':
            cmd = "reboot"
        elif key == 'q':
            running = False
            break

        if cmd:
            cmd_history.append(cmd)
            conn.sendall((cmd + "\n").encode())

        if time.time() - last_draw >= DRAW_INTERVAL:
            last_draw = time.time()
            draw()

    running = False


def main(stdscr: curses.window):
    global running, esp32_history
    global left_win, right_win

    init_ui(stdscr)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", PORT))
    server.listen(1)
    server.settimeout(0.5)

    esp32_history.append(f"Waiting for client on port {PORT}...")
    server_start_time = time.time()


    while running:
        try:
            conn, addr = server.accept()
            conn.settimeout(None)

            esp32_history.append(f"[Connected] {addr}")

            recv_thread = threading.Thread(
                target=receive_data,
                args=(conn,),
                daemon=True
            )
            recv_thread.start()

            try:
                command_loop(conn)
            except Exception as e:
                esp32_history.append(f"[Error] {e}")
            finally:
                conn.close()
                esp32_history = []
                esp32_history.append("[Disconnected]")

        except socket.timeout:
            elapsed = time.time() - server_start_time
            esp32_history = [
                f"Waiting for client on port {PORT}...",
                f"Time elapsed: {elapsed:.1f} seconds"
            ]

            ch = stdscr.getch()
            if ch != -1:
                key = curses.keyname(ch).decode("utf-8").lower()
                if key == 'q':
                    running = False

            draw()
            continue

    server.close()


if __name__ == "__main__":
    curses.wrapper(main)
