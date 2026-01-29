import pigpio
import threading
import time
import curses

from uart_handler import UARTHandler

# UART pins
TX = 23
RX = 24
BAUDRATE = 57600

running = True
output_lines = []
input_history = []


def init_ui(stdscr: curses.window):    
    curses.curs_set(1)
    stdscr.nodelay(True)

    height, width = stdscr.getmaxyx()
    mid = width // 2

    output_win = curses.newwin(height, mid, 0, 0)
    input_win = curses.newwin(height, mid, 0, mid)
    input_win.nodelay(True)
    input_win.keypad(True)

    return output_win, input_win


def draw_output(win: curses.window):
    global output_lines
    win.clear()
    h, w = win.getmaxyx()
    win.box()

    for i, line in enumerate(output_lines[-(h - 2):]):
        win.addstr(i + 1, 1, line[: w - 2])

    win.addstr(0, 2, "en ang1 | ang1 | vel1 | en ang2 | ang2 | vel2")
    win.refresh()


def draw_input(win: curses.window, input_buffer: str):
    global input_history
    win.clear()
    h, w = win.getmaxyx()
    win.box()
    
    for i, cmd in enumerate(input_history[-(h - 3):]):
        win.addstr(i + 1, 1, cmd[: w - 2])
    
    win.addstr(h - 2, 1, "> " + input_buffer[: w - 4])
    win.move(h - 2, 3 + len(input_buffer))
    win.refresh()


def receive_data(uart: UARTHandler):
    global running
    global output_lines
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
                output_lines.append(line)


def command(uart: UARTHandler, input_win: curses.window, output_win: curses.window):
    global running
    global output_lines
    global input_history
    input_buffer = ""

    input_history = [
        "----------------------------------------------",
        "        ESP32 Motor Controller (UART)         ",
        "----------------------------------------------",
        "  Format: [motor id][a|v][value] ",
        "                 <Examples>",
        "  1v5.1    : set velocity of motor 1 to 5.1",
        "  2a0.5    : set angle of motor 2 to 0.5",
        "  q       : quit",
        "-----------------------------------------------",
    ]

    while running:
        draw_input(input_win, input_buffer)
        draw_output(output_win)
        
        try:
            ch = input_win.getch()
        except:
            ch = -1

        if ch == -1:
            time.sleep(0.05)
            continue

        elif ch in (curses.KEY_BACKSPACE, 127):
            input_buffer = input_buffer[:-1]

        elif 32 <= ch <= 126:
            input_buffer += chr(ch)
        
        elif ch in (10, 13):
            cmd = input_buffer.strip()
            input_buffer = ""

            if not cmd:
                continue
            
            input_history.append(cmd) 

            if cmd.lower() == "q":
                running = False
                continue

            uart.println(cmd)


    running = False
    uart.destroy()


def main(stdscr: curses.window):
    global output_lines
    global input_history

    try:
        uart = UARTHandler(TX, RX, BAUDRATE)
    except Exception as e:
        print("UART init failed:", e)
        return

    output_win, input_win = init_ui(stdscr)

    output_lines.append("UART opened!")
    draw_output(output_win)

    # Start receiving thread
    t = threading.Thread(target=receive_data, args=(uart,))
    t.daemon = True
    t.start()
    
    time.sleep(1)
    uart.println("hi")

    command(uart, input_win, output_win)


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except Exception as e:
        print("CRASH:", e)
        import traceback
        traceback.print_exc()
