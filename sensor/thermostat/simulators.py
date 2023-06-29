import threading
from time import sleep
from .config import Config
from .data import Data

import logging
log = logging.getLogger(__name__)

class Simulator:

    WORKER_THREAD_NAME = "sim-worker"

    def __init__(self, config:Config) -> None:
        self._config = config
        self.thread_name = Simulator.WORKER_THREAD_NAME
        self.interval = config.temperature_change_interval

        self.shutdown = threading.Event()
        self.shutdown.clear()

    def worker(self):
        while True:
            if self.shutdown.is_set():
                log.debug("Shutdown Flag is set. Stopping...")
                return
            
            sleep(5)