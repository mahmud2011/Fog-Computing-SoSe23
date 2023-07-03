import logging
import threading
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
        self.sock.settimeout(0.5)
        self.sock.bind(('', MCAST_PORT))
        self.mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, self.mreq)

    def __init__(self, thread_name: str, config: Config) -> None:
        super().__init__(thread_name, config)

        self.setup_multicast_receiver()

        self.sensors:list[Sensor] = list()
        self.sensor_threads:list[threading.Thread] = list()

    def worker(self):
        while True:
            if self.shutdown.is_set():
                log.debug("Shutdown Flag is set. Stopping workers...")
                for sensor in self.sensors:
                    log.info(f"Shutting Down {sensor._type} sensor at {sensor._address}")
                    sensor.shutdown.set()
                for thread in self.sensor_threads:
                    log.info(f"Joining keepalive worker for {sensor._type} sensor at {sensor._address}")
                    thread.join()
                return
            
            try:
                while True:
                    data_received, address_sender = self.sock.recvfrom(10240)
                    log.debug(f"received: {data_received}\nfrom: {address_sender}")
                    data_rcv_list = data_received.decode("ascii").split(":")
                    log.debug(f"Decoded data: {data_rcv_list}")
                    if data_rcv_list[0] == "SENSOR":
                        sensor_type = data_rcv_list[1]
                        sensor_port = int(data_rcv_list[2])
                        sensor_ip = address_sender[0]

                        already_exists = False
                        for sensor in self.sensors:
                            if sensor._ip == sensor_ip and sensor._port == sensor_port:
                                already_exists = True
                                log.debug("Sensor already exists...")
                                if sensor.offline == True:
                                    log.info(f"Restarting worker for {new_sensor._type} at {new_sensor._address}")
                                    self.sensor_threads.remove(sensor._own_thread)
                                    sensor._own_thread.join()
                                    t = threading.Thread(target = new_sensor.keep_alive_worker, name=f"sensor-worker-{new_sensor._type}-{new_sensor._address}")
                                    self.sensor_threads.append(t)
                                    sensor._own_thread = t
                                    t.start()

                    
                        if not already_exists:
                            log.info(f"Adding new {sensor_type} sensor at {sensor_ip}:{sensor_port}")
                            new_sensor = Sensor(self._config, sensor_ip, sensor_port, sensor_type)
                            self.sensors.append(new_sensor)
                            log.info(f"Starting worker for {new_sensor._type} at {new_sensor._address}")
                            t = threading.Thread(target = new_sensor.keep_alive_worker, name=f"sensor-worker-{new_sensor._type}-{new_sensor._address}")
                            self.sensor_threads.append(t)
                            new_sensor._own_thread = t
                            t.start()
                        else:
                            pass

                    else:
                        pass

            except:
                log.debug("No multicast received...")

            self.shutdown.wait(5)