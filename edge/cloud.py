from websockets.sync.client import connect
from websockets.exceptions import ConnectionClosed

from edge.config import Config
from .worker import Worker

import logging

log = logging.getLogger(__name__)

class CloudConfigurationWebsocket(Worker):
    

    def __init__(self, thread_name: str, config: Config, address: str) -> None:
        super().__init__(thread_name, config)

        self._addr = address

    def worker(self):
        with connect(self._addr) as websocket:
            while (True):
                if self.shutdown.is_set():
                    log.debug("Shutdown Flag is set. Stopping...")
                    return
                
                try:
                    websocket.recv()
                except ConnectionClosed:
                    pass


class CloudDataQueue:
    pass

