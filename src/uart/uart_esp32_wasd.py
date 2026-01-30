import curses 
from uart.uart_handler import UARTHandler
import threading
import time


# UART pins
TX = 23
RX = 24
BAUDRATE = 57600

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
    right_win = curses.newwin(height, mid, 0, mid)

    # Right window checks keyboard with no blockings
    right_win.timeout(10)
    right_win.keypad(True)


def draw():
    """
    Draws left and right windows with current status.
    1. Left window shows instructions, command history, 
        current azimuth/elevation, and last key pressed.
    2. Right window shows ESP32 response history.
    """
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
        "Q: Quit",
    ]
    
    i = 0
    for line in instructions:
        left_win.addstr(i + 1, 1, line[: w - 2])
        i += 1

    rem = h - 2 - i
    for line in cmd_history[-rem:]:
        left_win.addstr(i + 1, 1, line[: w - 2])
        i += 1
    
    if not key:
        key = "No key pressed"

    left_win.addstr(h - 3, 1, f"Azimuth: {azimuth:.2f} Elevation: {elevation:.2f}")
    left_win.addstr(h - 2, 1, "Key: " + key)
    left_win.refresh()

    right_win.clear()
    h, w = right_win.getmaxyx()
    right_win.box()

    for i, line in enumerate(esp32_history[-(h - 2):]):
        right_win.addstr(i + 1, 1, line[: w - 2])

    right_win.addstr(0, 2, "en ang1 | ang1 | vel1 | en ang2 | ang2 | vel2")
    right_win.refresh()


def receive_data(uart: UARTHandler):
    global running
    global esp32_history

    def on_receive(line: str):
        esp32_history.append(line)

    uart.listen(on_receive)


def command(uart: UARTHandler):
    global running
    global cmd_history, right_win
    global azimuth, elevation

    if right_win is None:
        return

    motor_enabled = False
    last_draw = time.time()

    while running:
        ch = right_win.getch()
        pressed_key = None
        cmd = None

        if ch != -1:
            pressed_key = curses.keyname(ch).decode("utf-8")

        if pressed_key == 'w':
            elevation += MOVEMENT_STEP
            cmd = "1a" + f"{elevation:.2f}"
        elif pressed_key == 's':
            elevation -= MOVEMENT_STEP
            cmd = "1a" + f"{elevation:.2f}"
        elif pressed_key == 'a':
            azimuth -= MOVEMENT_STEP
            cmd = "2a" + f"{elevation:.2f}"
        elif pressed_key == 'd':
            azimuth += MOVEMENT_STEP
            cmd = "2a" + f"{elevation:.2f}"

        elif pressed_key == 'z':
            azimuth = 0.0
            elevation = 0.0
            cmd = "zero"

        elif pressed_key == ' ':
            motor_enabled = not motor_enabled
            if motor_enabled:
                cmd = "enable"
            else:
                cmd = "disable"

        elif pressed_key == 'q':
            running = False

        if not cmd is None:
            cmd_history.append(cmd)
            uart.println(cmd)

        if time.time() - last_draw >= DRAW_INTERVAL:
            last_draw = time.time()
            draw()

    running = False


def main(stdscr):
    try:
        uart = UARTHandler(TX, RX, BAUDRATE)
    except Exception as e:
        print("UART init failed:", e)
        return

    init_ui(stdscr)

    # Start receiving thread
    t = threading.Thread(target=receive_data, args=(uart,))
    t.daemon = True
    t.start()
    
    time.sleep(1)
    uart.println("hi")

    command(uart)


if __name__ == "__main__":
    curses.wrapper(main)