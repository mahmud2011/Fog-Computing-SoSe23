import datetime
import requests

import logging

log = logging.getLogger(__name__)

class Sensor:

    def __init__(self, ip:str, port:int, type:str) -> None:
        self._ip = ip
        self._port = port
        self._type = type
        self._alive = False
        self._address = f'http://{self._ip}:{self._port}'

        self.last_connection = datetime.datetime.now()

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
            r = requests.get(f"{self._address}/alive", timeout=3)
            self.connected_to_sensor()
            if not self._alive:
                log.info(f"(Re)Connected to {self._type} at {self._address}")
                self._alive = True
        except:
            log.debug(f"Failed to connect to Sending keepalive to {self._address}/alive")
            if self._alive:
                log.info(f"Failed to connect to {self._type} sensor at {self._address}")
                self._alive = False

    def keep_alive_worker(self):
        pass