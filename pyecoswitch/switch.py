import socket
import struct, time
import pprint
from threading import Thread, Event
import random

class EcoSwitch(object):
    def __init__(self, data):
        self.switch_data = data
        self.name = data[3].decode('utf-8')

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.connect((self.switch_data[-2], self.switch_data[-1]))

        self.pending = {}

        self.running = True
        self.thread = Thread(target=self.recv_thread)
        self.thread.start()

    def __repr__(self):
        def class_decor(s):
            return '## %s ##' %s
        return pprint.pformat(
                (class_decor(self.__class__.__name__), self.switch_data[3])
                )

    def stop(self):
        self.running = False
        self.thread.join()

    def recv_thread(self):
        while self.running:
            try:
                self.socket.settimeout(0.5)
                data = self.socket.recv(1000)
                self.socket.settimeout(None)
                
                xid, payload_length = struct.unpack_from('<HH', data, 6)
                payload = bytearray(data[128: 128 + payload_length])
                data = bytearray(data[:128])

                if xid in self.pending:
                    _, _, cb = self.pending[xid]
                    del(self.pending[xid])
                    if cb: cb(data, payload)

            except socket.timeout:
                continue

    def xmit(self, data):
        #self.socket.sendto(data, (self.switch_data[-2], self.switch_data[-1]))
        self.socket.send(data)

    def send_payload(self, flags, command, data, cb = None):
        xid = random.randint(0, 65535)
        main_body = struct.pack('<HLHH6s32s32s32sLLLL',
                flags,
                command,
                xid,
                len(data),
                self.switch_data[1],
                self.switch_data[2],
                self.switch_data[3],
                self.switch_data[4],
                0,      # The switch returns data in this field
                int(time.time() * 1000) & 0xffffffff,
                0,
                0x0d5249ae)

        self.pending[xid] = (main_body, data, cb)
        self.xmit(main_body + data)
        self.xmit(main_body + data)
        self.xmit(main_body + data)

    def turn_on(self):
        self.send_payload(0x16, 0x05, b'\x01\x01')

    def turn_off(self):
        self.send_payload(0x16, 0x05, b'\x01\x00')

    def is_on(self):
        e = Event()
        state = [ False ]
        def cb(packet, payload):
            state[0] = payload[1] == 1
            e.set()
        self.send_payload(0x17, 0x05, b'', cb)
        e.wait()
        return state[0]
