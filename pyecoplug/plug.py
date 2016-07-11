import socket
import struct, time
import pprint
from threading import Thread, Event
import random

class EcoPlug(object):
    CONNECTION_TIMEOUT = 60

    def __init__(self, data):
        self.plug_data = data
        self.name = data[3].decode('utf-8')

        self._pending = {}

        self._connected = False
        self._connected_timeout = 0


    def __repr__(self):
        def class_decor(s):
            return '## %s ##' %s
        return pprint.pformat(
                (class_decor(self.__class__.__name__), self.plug_data[3])
                )

    def _connect(self):
        if self._connected:
            self._connected_timeout = time.time() + self.CONNECTION_TIMEOUT
            return

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.connect((self.plug_data[-2], self.plug_data[-1]))

        self._connected = True
        self._connected_timeout = time.time() + self.CONNECTION_TIMEOUT

        self._start()

    def _timeout_connection(self, from_recv_thread=False):
        if not self._connected or time.time() < self._connected_timeout:
            return False

        # The timeout has occurred
        # stop the thread
        if not from_recv_thread:
            self._stop()
        else:
            self._running = False

        # close the connection
        self._socket.close()
        self._connected = False

        return True

    def _start(self):
        self._pending = {}
        self._running = True
        self._thread = Thread(target=self._recv_thread)
        self._thread.start()

    def _stop(self):
        self._running = False
        self._thread.join()

    def stop(self):
        if self._connected:
           self._connected = False
           self._stop()
           self._socket.close()

    def _recv_thread(self):
        while self._running:
            if self._timeout_connection(True):
                break

            try:
                self._socket.settimeout(0.1)
                data = self._socket.recv(1000)
                self._socket.settimeout(None)
                
                xid, payload_length = struct.unpack_from('<HH', data, 6)
                payload = bytearray(data[128: 128 + payload_length])
                data = bytearray(data[:128])

                if xid in self._pending:
                    _, _, cb = self._pending[xid]
                    del(self._pending[xid])
                    if cb: cb(data, payload)

            except socket.timeout:
                continue

    def xmit(self, data):
        self._socket.send(data)

    def send_payload(self, flags, command, data, cb = None):
        xid = random.randint(0, 65535)
        main_body = struct.pack('<HLHH6s32s32s32sLLLL',
                flags,
                command,
                xid,
                len(data),
                self.plug_data[1],
                self.plug_data[2],
                self.plug_data[3],
                self.plug_data[4],
                0,      # The plug returns data in this field
                int(time.time() * 1000) & 0xffffffff,
                0,
                0x0d5249ae)

        self._pending[xid] = (main_body, data, cb)
        self.xmit(main_body + data)
        self.xmit(main_body + data)
        self.xmit(main_body + data)

    def turn_on(self):
        self._connect()
        self.send_payload(0x16, 0x05, b'\x01\x01')

    def turn_off(self):
        self._connect()
        self.send_payload(0x16, 0x05, b'\x01\x00')

    def is_on(self):
        self._connect()

        # create an event which we can wait upon
        e = Event()
        state = [ False ]
        def cb(packet, payload):
            state[0] = payload[1] == 1
            e.set()
        self.send_payload(0x17, 0x05, b'', cb)
        e.wait()
        return state[0]
