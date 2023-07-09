import json
import logging
from math import sqrt
import os
import threading
from time import sleep
from edge.config import Config
from .worker import Worker
import requests
import datetime

import socket
import struct

log = logging.getLogger(__name__)

class Sensor:

    def __init__(self, config:Config, ip:str, port:int, type:str, sensormanager) -> None:
        self._config = config
        self._sensormanager:SensorManager = sensormanager

        self._ip = ip
        self._port = port
        self._type = type
        self._alive = False
        self._address = f'http://{self._ip}:{self._port}'

        self.last_connection = datetime.datetime.fromtimestamp(1)

        self.shutdown = threading.Event()
        self.shutdown.clear()
        self._own_thread:threading.Thread = None

        self.exponential_backoff = 0
        self.offline = False

        self.new_config = threading.Event()
        self.new_config.set()
        self.target_temp = 25




    def connected_to_sensor(self):
        self.last_connection = datetime.datetime.now()

    def request_data(self):
        log.debug(f"Getting data from {self._address}/data")
        if not self._alive:
            return None
        try:
            r = requests.get(f"{self._address}/data", timeout=1)
            self.connected_to_sensor()
            return r
        except:
            self.is_alive()
            return None



    def get_valve(self) -> requests.Response:
        log.debug(f"Getting valve configuration from {self._address}/configuration/valve")
        if not self._alive:
            return None
        try:
            r = requests.get(f"{self._address}/configuration/valve", timeout=1)
            self.connected_to_sensor()
            return r
        except:
            self.is_alive()
            return None

    def set_valve(self, configuration) -> bool:
        log.debug(f"Setting valve configuration for {self._address}/configuration/valve")
        if not self._alive:
            return None
        try:
            headers = {"Content-Type": "application/json"}
            r = requests.post(f"{self._address}/configuration/valve", json=configuration, headers=headers, timeout=1)
            self.connected_to_sensor()
            return r
        except:
            self.is_alive()
            return None

    def update_valve(self):
        # get temp
        response: requests.Response = self.request_data()
        current_temp = json.loads(response.content.decode())['temperature']
        #check if temp == target
        if self.target_temp == current_temp:
            log.debug("Thermostat has already reached target temperature")
            return
        log.info(f"Updating valve configuration for {self._type} at {self._address}")
        #calc valve
        target_valve = int(((self.target_temp - 15) / 10) * 100)
        #set valve
        configuration = {'valve':target_valve}
        self.set_valve(configuration)

    def is_alive(self):
        log.debug(f"Sending keepalive to {self._address}/alive")
        try:
            r = requests.get(f"{self._address}/alive", timeout=1)
            self.connected_to_sensor()
            if not self._alive:
                log.info(f"(Re)Connected to {self._type} at {self._address}")
                self._alive = True
        except:
            log.debug(f"Failed to connect when sending a request to {self._address}/alive")
            if self._alive:
                log.info(f"Failed to connect to {self._type} sensor at {self._address}")
                self._alive = False

    def keep_alive_worker(self):
        while True:
            if self.shutdown.is_set():
                log.debug("Shutdown Flag is set. Stopping...")
                return
            
            if (datetime.datetime.now() - self.last_connection).total_seconds()  > self._config.keepalive_interval:
                self.is_alive()
            
            if not self._alive:
                self.exponential_backoff += 1

            if self._alive:

                #update config
                if self.new_config.is_set():
                    self.target_temp = self._sensormanager.sensor_config['target_temperature']
                    
                    self.new_config.clear()

                self.update_valve()
                

                self.shutdown.wait(self._config.keepalive_worker_interval)




            elif self.exponential_backoff > self._config.max_backoffs:
                log.info(f"Exceeded maximum backoffs {self._type} sensor at {self._address}")
                self.exponential_backoff = 0
                self.offline = True
                return
            else:
                backoff_time = round((self._config.keepalive_worker_interval) * sqrt(self.exponential_backoff), 2)
                log.info(f"Backing off for {backoff_time} seconds for {self._type} sensor at {self._address}")
                self.shutdown.wait(backoff_time)

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

        self._sensor_config = {'target_temperature':21}
        self._config_lock = threading.Lock()

        self._sensor_config_file = os.path.join(self._config.data_path, 'sensor_config')

        if os.path.exists(self._sensor_config_file) and os.path.isfile(self._sensor_config_file):
                file = open(self._sensor_config_file, 'r')
                self._sensor_config = file.read()
                log.info("Loaded id from file")
                file.close()
                log.info("Loaded sensor config from file")

    @property
    def sensor_config(self):
        with self._config_lock:
            return self._sensor_config
        
    @sensor_config.setter
    def sensor_config(self, value):
        with self._config_lock:
            self._sensor_config = value 
            for sensor in self.sensors:
                sensor.new_config.set()
            file = open(self._sensor_config_file, "w")
            file.write(json.dumps(self._sensor_config))
            file.close()

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
                self.sock.close()
                return
            

            
            # Check for new multicast messages
            try:
                while True:
                    # Receive Data
                    data_received, address_sender = self.sock.recvfrom(10240)
                    log.debug(f"received: {data_received}\nfrom: {address_sender}")
                    data_rcv_list = data_received.decode("ascii").split(":")
                    log.debug(f"Decoded data: {data_rcv_list}")
                    # Data is a message from the sensor
                    if data_rcv_list[0] == "SENSOR":
                        sensor_type = data_rcv_list[1]
                        sensor_port = int(data_rcv_list[2])
                        sensor_ip = address_sender[0]

                        already_exists = False
                        for sensor in self.sensors:
                            if sensor._ip == sensor_ip and sensor._port == sensor_port:
                                # The sensor is known
                                already_exists = True
                                log.debug("Sensor already exists...")
                                if sensor.offline == True:
                                    # It is marked as offline (we currently do not get data from them)
                                    # We reactivate the Sensor worker
                                    log.info(f"Restarting worker for {sensor._type} at {sensor._address}")
                                    self.sensor_threads.remove(sensor._own_thread)
                                    sensor._own_thread.join()
                                    t = threading.Thread(target = new_sensor.keep_alive_worker, name=f"sensor-worker-{sensor._type}-{sensor._address}")
                                    self.sensor_threads.append(t)
                                    sensor._own_thread = t
                                    sensor.offline = False
                                    sensor.new_config.set()
                                    t.start()
                                    

                    
                        if not already_exists:
                            # The sensor is unknown and we create a new Sensor instance
                            log.info(f"Adding new {sensor_type} sensor at {sensor_ip}:{sensor_port}")
                            new_sensor = Sensor(self._config, sensor_ip, sensor_port, sensor_type, self)
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

            except TimeoutError:
                # The receive failed (timeout)
                log.debug("No multicast received...")

            self.shutdown.wait(5)



