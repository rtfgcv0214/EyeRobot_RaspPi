from typing import Callable, Optional


def listen(conn, 
           callback: Callable[[str], None], 
           separator: Optional[str] ="\n", 
           is_running: Optional[Callable[[], bool]] = lambda: True):
    """
    Continuously listen to socket and call the callback function
    when data is received. If separator is specified, the callback is called
    only when the separator is found in the received data.
    """
    buffer = ""

    while is_running():
        try:
            data = conn.recv(1024)
        except:
            break

        if not data:
            break  # connection closed

        chunk = data.decode()

        if separator is None:
            callback(chunk.strip())
            continue

        buffer += chunk

        while separator in buffer:
            line, buffer = buffer.split(separator, 1)
            if line:
                callback(line)
