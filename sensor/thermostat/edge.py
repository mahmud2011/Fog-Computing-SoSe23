import datetime
import logging
import threading
from time import sleep

from .config import Config
from .simulators import Simulator

import socket

log = logging.getLogger(__name__)

class EdgeContext(Simulator):

    WORKER_THREAD_NAME = "edge-alive-worker"

    def __init__(self, config: Config) -> None:
        super().__init__(config=config)

        self.thread_name = EdgeContext.WORKER_THREAD_NAME

        self.contextlock = threading.Lock()

        self.edgeavailable = False
        self.lastseen:datetime.datetime = datetime.datetime.fromtimestamp(1)

    
    def edge_seen(self):
        with self.contextlock:
            self.lastseen = datetime.datetime.now()


    def send_multicast(self):
        """
        based on: https://blog.finxter.com/how-to-send-udp-multicast-in-python/
        last-visited: 02.07.2023
        """
        group = '224.1.1.1'
        port = self._config.multicast_port
        # 2-hop restriction in network
        ttl = 2
        sock = socket.socket(socket.AF_INET,
                            socket.SOCK_DGRAM,
                            socket.IPPROTO_UDP)
        sock.setsockopt(socket.IPPROTO_IP,
                        socket.IP_MULTICAST_TTL,
                        ttl)
        sock.sendto(bytes(f"TSENSOR:{self._config.server_port}", encoding="ascii"), (group, port))

        log.info("Sent Multicast")

        sock.close()

    def worker(self):
        while True:
            if self.shutdown.is_set():
                log.debug("Shutdown Flag is set. Stopping...")
                return
            
            with self.contextlock:
                before = self.edgeavailable
                if (datetime.datetime.now() - self.lastseen).total_seconds()  < self._config.edge_search_timer:
                    self.edgeavailable = True
                else:
                    self.edgeavailable = False
                
                if before != self.edgeavailable:
                    log.info(f"Edge availability changed from {before} to {self.edgeavailable}")

            self.send_multicast()

            sleep(5)
        

