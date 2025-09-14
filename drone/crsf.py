import serial

class CRSF(object):
    def __init__(self, port="/dev/ttyS1", baudrate=420000):
        self.ser = serial.Serial(
            port = port, baudrate = baudrate,
            bytesize = serial.EIGHTBITS,
            parity = serial.PARITY_NONE,
            stopbits = serial.STOPBITS_ONE,
            timeout = 0.1
        )
        if not self.ser.is_open:
            self.ser.open()

    def process(self):
        if self.ser.in_waiting > 0:
            data = self.ser.read(self.ser.in_waiting)
            print(f"Received from CRSF: {data}")


    def send(self, data: bytes):