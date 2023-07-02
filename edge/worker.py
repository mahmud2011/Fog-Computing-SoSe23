import logging
import threading
from time import sleep
from .config import Config

log = logging.getLogger(__name__)

class Worker:

    def __init__(self, thread_name: str, config: Config) -> None:
        self._thread_name = thread_name
        self._config = config

        self.shutdown = threading.Event()
        self.shutdown.clear()

    @property
    def thread_name(self):
        return self._thread_name

    def worker(self):
        while True:
            if self.shutdown.is_set():
                log.debug("Shutdown Flag is set. Stopping...")
                return
            
            sleep(5)