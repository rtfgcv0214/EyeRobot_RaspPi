import pigpio
import threading
import time
import curses

TX = 23
RX = 24
BAUDRATE = 57600

ANGLE_STEP = 0.05   # rad per key press
SEND_INTERVAL = 0.05  # seconds

running = True
output_lines = []

motor1_angle = 0.0
motor2_angle = 0.0
key_state = set()


def init_uart():
    pi = pigpio.pi()
    pi.bb_serial_read_open(RX, BAUDRATE)
    pi.set_mode(TX, pigpio.OUTPUT)
    return pi


def bb_write(pi, data: bytes):
    pi.wave_add_serial(TX, BAUDRATE, data)
    wid = pi.wave_create()
    pi.wave_send_once(wid)

    while pi.wave_tx_busy():
        time.sleep(0.001)

    pi.wave_delete(wid)


def receive_data(pi):
    global output_lines
    buffer = ""

    while running:
        count, data = pi.bb_serial_read(RX)
        if count == 0:
            time.sleep(0.01)
            continue

        chunk = data.decode("utf-8", errors="ignore").replace("\x00", "")
        buffer += chunk

        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            line = line.strip()
            if line:
                output_lines.append(line)
                output_lines = output_lines[-100:]


def draw(win):
    win.clear()
    h, w = win.getmaxyx()
    win.box()

    # output
    for i, line in enumerate(output_lines[-(h - 3):]):
        win.addstr(i + 1, 1, line[: w - 2])

    status = f"M1: {motor1_angle:.2f} rad | M2: {motor2_angle:.2f} rad | WASD move | q quit"
    win.addstr(h - 2, 1, status[: w - 2])
    win.refresh()


def control_loop(pi):
    global motor1_angle, motor2_angle

    while running:
        updated1 = False
        updated2 = False

        if 'w' in key_state:
            motor2_angle += ANGLE_STEP
            updated2 = True
        if 's' in key_state:
            motor2_angle -= ANGLE_STEP
            updated2 = True
        if 'a' in key_state:
            motor1_angle -= ANGLE_STEP
            updated1 = True
        if 'd' in key_state:
            motor1_angle += ANGLE_STEP
            updated1 = True

        if updated1:
            cmd = f"1a{motor1_angle:.3f}\n"
            bb_write(pi, cmd.encode())
        
        if updated2:
            cmd = f"2a{motor2_angle:.3f}\n"
            bb_write(pi, cmd.encode())

        time.sleep(SEND_INTERVAL)


def main(stdscr):
    global running

    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.keypad(True)

    pi = init_uart()

    t_rx = threading.Thread(target=receive_data, args=(pi,), daemon=True)
    t_rx.start()

    t_ctrl = threading.Thread(target=control_loop, args=(pi,), daemon=True)
    t_ctrl.start()

    bb_write(pi, b"hi\n")

    while running:
        draw(stdscr)

        try:
            ch = stdscr.getch()
        except:
            ch = -1

        if ch == -1:
            time.sleep(0.01)
            continue

        if ch == ord('q'):
            running = False
            break

        if chr(ch) in ['w', 'a', 's', 'd']:
            key_state.add(chr(ch))

        if ch == curses.KEY_RESIZE:
            continue

        # key release detection (best-effort)
        if ch == -1:
            key_state.clear()

    pi.bb_serial_read_close(RX)
    pi.stop()


if __name__ == "__main__":
    curses.wrapper(main)
