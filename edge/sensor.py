from math import sqrt
from time import sleep
import datetime
import threading
import requests

import logging

from .config import Config

log = logging.getLogger(__name__)

class Sensor:

    def __init__(self, config:Config, ip:str, port:int, type:str) -> None:
        self._config = config

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



    def connected_to_sensor(self):
        self.last_connection = datetime.datetime.now()

    def request_data(self) -> str:
        pass

    def get_valve(self) -> str:
        pass

    def set_valve(self, configuration:str):
        pass

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