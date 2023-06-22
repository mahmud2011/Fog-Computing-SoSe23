import datetime
import logging
import threading
from time import sleep
from .config import Config
from .data import Data

log = logging.getLogger(__name__)

class TemperatureSimulator:

    WORKER_THREAD_NAME = "temperature-worker"

    def __init__(self, config:Config, data:Data) -> None:
        self._config = config
        self._data = data
        self.thread_name = TemperatureSimulator.WORKER_THREAD_NAME

        self.shutdown = threading.Event()
        self.shutdown.clear()

    def worker(self):
        while True:
            if self.shutdown.is_set():
                log.debug("Shutdown Flag is set. Stopping...")
                return
            
            self._data.add_data(datetime.datetime.now(), {"temp":23.3})
            log.debug("Temperature Sim has written data")
            
            sleep(5)