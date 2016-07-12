import socket
from datetime import datetime
import struct, time
from threading import Thread
from .plug import EcoPlug

def normalize_string(x):
    if type(x) == bytes:
        return x.rstrip(b' \t\r\n\0')
    return x

class EcoDiscovery(object):
    UDP_PORT = 8900

    def __init__(self, on_add, on_remove):
        self.on_add = on_add
        self.on_remove = on_remove
        self.discovered = {}

        self.running = False

    def iterate(self):
        for m, p in self.discovered.items():
            yield p[1]

    def start(self):
        self.running = True
        self.thread = Thread(target=self.poll_discovery)

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('0.0.0.0', self.UDP_PORT))
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.socket.settimeout(0.5)

        self.thread.start()

    def stop(self):
        self.running = False
        self.thread.join()
        for m, p in self.discovered.items():
            self.on_remove(p[1])
            p[1].stop()
        self.discovered.clear()
        self.socket.close()

    def process_packet(self, pkt):
        now = time.time()
        mac_addr = pkt[-3]
        if not mac_addr in self.discovered:
            plug = EcoPlug(pkt)
            self.on_add(plug)
            self.discovered[mac_addr] = (now, plug)
        else:
            plug = self.discovered[mac_addr][1]
            plug.plug_data = pkt
            self.discovered[mac_addr] = (now, plug)

    def prune_stale(self):
        now = time.time()
        to_remove = []
        for mac, p in self.discovered.items():
            if now - p[0] >= 30:
                to_remove.append(mac)
        for mac in to_remove:
            plug = self.discovered[mac][1]
            self.on_remove(plug)
            plug.stop()
            del(self.discovered[mac])

    def poll_discovery(self):
        broadcast = True
        while self.running:
            if broadcast:
                last_broadcast = time.time()

                now = datetime.now()
                packet = bytearray(b'\x00' * 128)
                struct.pack_into('<HBBL', packet, 24, now.year, now.month, now.day, now.hour * 3600 + now.minute * 60 + now.second)
                self.socket.sendto(packet, ('255.255.255.255', 5888))
                self.socket.sendto(packet, ('255.255.255.255', 5888))
                self.socket.sendto(packet, ('255.255.255.255', 5888))
                self.socket.sendto(packet, ('255.255.255.255', 25))
                self.socket.sendto(packet, ('255.255.255.255', 25))
                self.socket.sendto(packet, ('255.255.255.255', 25))

                broadcast = False

            elif time.time() - last_broadcast >= 10:
                broadcast = True

            else:
                try:
                    data, _ = self.socket.recvfrom(408)
                    pkt = list(struct.unpack('<L6s32s32s32sHHBBLl64s64sH10s12s16s16s16sLLLLH30s18s18sL', data))
                    pkt = tuple([normalize_string(x) for x in pkt])
                    self.process_packet(pkt)

                except socket.timeout:
                    continue
                finally:
                    self.prune_stale()


if __name__ == '__main__':
    def on_add(pkt):
        print('Add:', repr(pkt))
        pkt.turn_on()
        print(pkt.is_on())
    def on_remove(pkt):
        print('Remove:', repr(pkt))

    try:
        e = EcoDiscovery(on_add, on_remove)
        e.start()
        time.sleep(180)
    finally:
        for plug in e.iterate():
            plug.turn_off()
        e.stop()


