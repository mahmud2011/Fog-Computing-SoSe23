import logging
from time import sleep
from edge.config import Config
from .worker import Worker
from .sensor import Sensor

import socket
import struct

log = logging.getLogger(__name__)

class SensorManager(Worker):

    def setup_multicast_receiver(self):
        """
        based on: https://blog.finxter.com/how-to-send-udp-multicast-in-python/
        last-visited: 02.07.2023
        """

        MCAST_GRP = '224.1.1.1'
        MCAST_PORT = self._config.multicast_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setblocking(False)
        self.sock.settimeout(1.0)
        self.sock.bind(('', MCAST_PORT))
        self.mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, self.mreq)

    def __init__(self, thread_name: str, config: Config) -> None:
        super().__init__(thread_name, config)

        self.setup_multicast_receiver()

        self.sensors:list[Sensor] = list()
        self.sensor_threads = list()

    def worker(self):
        while True:
            if self.shutdown.is_set():
                log.debug("Shutdown Flag is set. Stopping...")
                return
            
            try:
                while True:
                    data_rcv, address_rcv = self.sock.recvfrom(10240)
                    log.debug(f"received: {data_rcv}\nfrom: {address_rcv}")
                    data_rcv_list = data_rcv.decode("ascii").split(":")
                    log.debug(f"Decoded data: {data_rcv_list}")
                    if data_rcv_list[0] == "SENSOR":
                        sensor_type = data_rcv_list[1]
                        sensor_port = int(data_rcv_list[2])
                        sensor_ip = address_rcv[0]

                        already_exists = False
                        for sensor in self.sensors:
                            if sensor._ip == sensor_ip and sensor._port == sensor_port:
                                already_exists = True
                    
                        if not already_exists:
                            log.info(f"Adding new {sensor_type} sensor at {sensor_ip}:{sensor_port}")
                            new_sensor = Sensor(sensor_ip, sensor_port, sensor_type)
                            self.sensors.append(new_sensor)
                            new_sensor.is_alive()
                        else:
                            log.debug("Sensor already exists...")

                    else:
                        pass

            except:
                log.debug("No multicast received...")
            
            sleep(5)