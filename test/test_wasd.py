import curses 


MOVEMENT_STEP = 0.02
running = True
status_history = []


def init_ui(stdscr: curses.window):    
    curses.curs_set(1)
    stdscr.nodelay(True)

    height, width = stdscr.getmaxyx()
    mid = width // 2

    left_win = curses.newwin(height, mid, 0, 0)
    right_win = curses.newwin(height, mid, 0, mid)

    # Right window checks keyboard with no blockings
    right_win.timeout(10)
    right_win.keypad(True)

    return left_win, right_win


def draw(win: curses.window, key: str | None, azimuth: float, elevation: float):
    global status_history

    win.clear()
    h, w = win.getmaxyx()
    win.box()
    
    for i, cmd in enumerate(status_history[-(h - 4):]):
        win.addstr(i + 1, 1, cmd[: w - 2])
    
    if not key:
        key = "No key pressed"

    win.addstr(h - 3, 1, f"Azimuth: {azimuth:.2f} Elevation: {elevation:.2f}")
    win.addstr(h - 2, 1, "Key: " + key)
    win.refresh()


def command(win: curses.window):
    global running

    azimuth = 0.0
    elevation = 0.0
    motor_enabled = False

    while running:
        ch = win.getch()
        pressed_key = None

        if ch != -1:
            pressed_key = curses.keyname(ch).decode("utf-8")

        draw(win, pressed_key, azimuth, elevation)

        if pressed_key == 'w':
            elevation += MOVEMENT_STEP
        elif pressed_key == 's':
            elevation -= MOVEMENT_STEP
        elif pressed_key == 'a':
            azimuth -= MOVEMENT_STEP
        elif pressed_key == 'd':
            azimuth += MOVEMENT_STEP

        elif pressed_key == 'z':
            status_history.append("Zeroing azimuth/elevation")
            azimuth = 0.0
            elevation = 0.0

        elif pressed_key == ' ':
            motor_enabled = not motor_enabled
            if motor_enabled:
                status_history.append("Enabled motors")
            else:
                status_history.append("Disabled motors")

        elif pressed_key == 'q':
            break

    running = False


def main(stdscr):
    left_win, right_win = init_ui(stdscr)

    instructions = [
        "Instructions:",
        "  space: enable/disable motors",
        "  Z: zero azimuth/elevation",
        "Controls:",
        "  W/S: Increase/Decrease Elevation",
        "  A/D: Decrease/Increase Azimuth",
        "  Q: Quit",
    ]

    left_win.clear()
    left_win.box()

    for i, line in enumerate(instructions):
        left_win.addstr(i + 1, 1, line)
    
    left_win.refresh()

    command(right_win)

if __name__ == "__main__":
    curses.wrapper(main)