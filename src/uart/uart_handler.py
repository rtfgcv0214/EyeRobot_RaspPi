import pigpio
import time


class UARTHandler:
    """
    Custom UART interface using PiPGIO module.
    Supports UART input/output with given tx and rx pins
    """
    TX = 23
    RX = 24
    BAUD = 57600

    def __init__(self, tx: int = TX, rx: int = RX, baud: int = BAUD):
        self.tx = tx
        self.rx = rx
        self.baud = baud
        self.pi = pigpio.pi()

        if not self.pi.connected:
            raise RuntimeError(
                "pigpio daemon not running. Try $sudo systemctl restart pigpiod"
            )

        self.pi.bb_serial_read_open(rx, baud)
        self.pi.set_mode(tx, pigpio.OUTPUT)
    
    
    def read(self, timeout: float | None = 0) -> str | None:
        """
        Read from UART input.

        timeout = 0     -> non-blocking
        timeout > 0     -> wait up to timeout seconds
        timeout = None  -> blocking
        """
        start = time.time()
        buffer = ""

        while True:
            try:
                count, data = self.pi.bb_serial_read(self.rx)
            except pigpio.error:
                return None

            if count > 0:
                chunk = data.decode("utf-8", errors="ignore").replace("\x00", "")
                return chunk

            # non-blocking
            if timeout == 0:
                return None

            # timed blocking
            if timeout is not None and (time.time() - start) > timeout:
                return None

            time.sleep(0.005)


    def write(self, data: bytes):
        """
        PiGPIO UART output handling
        """
        self.pi.wave_add_serial(self.tx, self.baud, data)

        wid = self.pi.wave_create()
        self.pi.wave_send_once(wid)

        while self.pi.wave_tx_busy():
            time.sleep(0.001)

        self.pi.wave_delete(wid)
    

    def println(self, string: str):
        self.write((string + "\n").encode('utf-8'))


    def destroy(self): 
        self.pi.bb_serial_read_close(self.rx)
        self.pi.stop()
