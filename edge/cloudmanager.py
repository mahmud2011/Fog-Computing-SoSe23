from math import sqrt
import datetime

import requests
from .config import Config
from .worker import Worker

from .cloud import CloudDataQueue, CloudConfigurationWebsocket
from .sensor import Sensor
from .sensormanager import SensorManager

import logging

log = logging.getLogger(__name__)


class CloudManager(Worker):

    def __init__(self, thread_name: str, config: Config, sensors: SensorManager) -> None:
        super().__init__(thread_name, config)
        self._ip = self._config.cloud_ip
        self._port = self._config.cloud_port
        self._address = f'http://{self._ip}:{self._port}'

        self._dataqueuemanager = CloudDataQueue()
        self._websocketmanager = CloudConfigurationWebsocket()

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
        except:
            log.debug(
                f"Failed to connect when sending a request to {self._address}/alive")
            if self._alive:
                log.info(f"Failed to connect to cloud at {self._address}")
                self._alive = False

    def keep_alive_worker(self):
        while True:
            if self.shutdown.is_set():
                log.debug("Shutdown Flag is set. Stopping...")
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
