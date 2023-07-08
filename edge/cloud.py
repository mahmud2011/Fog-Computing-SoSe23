from collections import deque
import datetime
import json
from math import sqrt
import os
import threading
import time
import requests
from websockets.sync.client import connect
from websockets.exceptions import ConnectionClosed

from edge.config import Config

from .config import Config
from .worker import Worker
from .sensor import SensorManager

import logging

log = logging.getLogger(__name__)

class CloudConfigurationWebsocket(Worker):
    

    def __init__(self, thread_name: str, address: str, config: Config, sensormanager: SensorManager, cloudmanager) -> None:
        super().__init__(thread_name, config)

        self._addr = address

        self._sensormanager = sensormanager
        self._cloud_manager:CloudManager = cloudmanager

    def parse_config(data:str):
        return data

    def worker(self):
        with connect(self._addr) as websocket:
            while (True):
                if self.shutdown.is_set():
                    log.debug("Shutdown Flag is set. Stopping...")
                    return
                
                try:
                    data = websocket.recv(0)

                    self._cloud_manager.connected_to_cloud()

                    parsed_data = CloudConfigurationWebsocket.parse_config(data)

                    self._sensormanager.sensor_config = parsed_data


                    
                except ConnectionClosed:
                    self._cloud_manager.is_alive()
                    #TODO connection closed softlocks this worker
                except TimeoutError:
                    self.shutdown.wait(5)


class CloudDataQueue(Worker):
    
    class DequeEncoder(json.JSONEncoder):
        """
        code from https://stackoverflow.com/questions/56631350/how-to-send-a-deque-collection-via-flask-in-python
        """

        def default(self, obj):
            if isinstance(obj, deque):
                return list(obj)
            return json.JSONEncoder.default(self, obj)

    def __init__(self, thread_name: str, config: Config, address: str) -> None:
        super().__init__(thread_name, config)

        self._addr = address

        self.datafile = os.path.join(self._config.data_path, 'data.json')

        self.datafilelock = threading.Lock()

        with self.datafilelock:

            if os.path.exists(self.datafile) and os.path.isfile(self.datafile):
                file = open(self.datafile, "r")
                datalist = json.loads(file.read())
                self.dataqueue = deque(
                    datalist, maxlen=self._config.buffer_maxlen)
                file.close
            else:
                self.dataqueue = deque(maxlen=self._config.buffer_maxlen)
                file = open(self.datafile, "x")
                file.write(json.dumps(self.dataqueue, cls=CloudDataQueue.DequeEncoder))
                file.close()

    def send_data_to_cloud(self):
        pass

    def get_data_from_cloud(self):
        pass

    def add_data(self, values: dict):
        with self.datafilelock:

            self.dataqueue.append(values)

            file = open(self.datafile, "w")
            file.write(json.dumps(self.dataqueue, cls=CloudDataQueue.DequeEncoder))
            file.close()
            
            log.debug("Saved data to File")

    def get_data(self):
        with self.datafilelock:

            return self.dataqueue[0]
        
    def confirm_sent_data(self):
        with self.datafilelock:

            data = self.dataqueue.popleft()
            file = open(self.datafile, "w")
            file.write(json.dumps(self.dataqueue, cls=CloudDataQueue.DequeEncoder))
            file.close()
            log.debug(f"Confirmed sending of {data}")


    def worker(self):
        while True:
            if self.shutdown.is_set():
                log.debug("Shutdown Flag is set. Stopping...")
                return
            
            log.info("Sending data in Buffer...")
            log.debug(f"Buffer: {self.dataqueue}")

            if len(self.dataqueue) > 5:
                while len(self.dataqueue) > 0:
                    self.get_data()
                    self.send_data_to_cloud()
                    self.confirm_sent_data()
                    time.sleep(0.5)
            
            

            self.shutdown.wait(5)


class CloudManager(Worker):

    def __init__(self, thread_name: str, config: Config, sensors: SensorManager) -> None:
        super().__init__(thread_name, config)
        self._ip = self._config.cloud_ip
        self._port = self._config.cloud_port
        self._address = f'http://{self._ip}:{self._port}'

        self._dataqueuemanager = CloudDataQueue('data-queue', config, self._address)
        self._websocketmanager = CloudConfigurationWebsocket('config-websocket', self._address, config, sensors, self)

        self.last_connection = datetime.datetime.fromtimestamp(1)
        self.alive = False
        self.exponential_backoff = 1


    def connected_to_cloud(self):
        self.last_connection = datetime.datetime.now()

    def is_alive(self):
        log.debug(f"Sending keepalive to {self._address}/alive")
        try:
            r = requests.get(f"{self._address}/alive", timeout=1)
            self.connected_to_cloud()
            if not self._alive:
                log.info(f"(Re)Connected to cloud at {self._address}")
                self._alive = True
                self._dataqueuemanager.shutdown.clear()
                t = threading.Thread(target = self._dataqueuemanager.worker, name=self._dataqueuemanager.thread_name)
                t.start()
                self._websocketmanager.shutdown.clear()
                t = threading.Thread(target = self._websocketmanager.worker, name=self._websocketmanager.thread_name)
                t.start()
        except:
            log.debug(
                f"Failed to connect when sending a request to {self._address}/alive")
            if self._alive:
                log.info(f"Failed to connect to cloud at {self._address}")
                self._alive = False
                self._dataqueuemanager.shutdown.set()
                self._websocketmanager.shutdown.set()

    def worker(self):
        while True:
            if self.shutdown.is_set():
                log.debug("Shutdown Flag is set. Stopping...")
                self._dataqueuemanager.shutdown.set()
                self._websocketmanager.shutdown.set()
                return

            if (datetime.datetime.now() - self.last_connection).total_seconds() > self._config.keepalive_interval:
                self.is_alive()

            if not self._alive and self.exponential_backoff < self._config.max_backoffs:
                self.exponential_backoff += 1

            if self._alive:
                self.exponential_backoff = 0
                self.shutdown.wait(self._config.keepalive_worker_interval)
            else:
                backoff_time = round(
                    (self._config.keepalive_worker_interval) * sqrt(self.exponential_backoff), 2)
                log.info(
                    f"Backing off for {backoff_time} seconds for cloud at {self._address}")
                self.shutdown.wait(backoff_time)