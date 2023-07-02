
from .worker import Worker

import logging
import threading

log = logging.getLogger(__name__)

class WorkerManager:

    def __init__(self, config, workers:list[Worker]) -> None:
        self._config = config
        self._workers = workers
        self._threads:list[threading.Thread] = list()

    async def process_startup(self, scope, event):
        log.info("Starting Up Workers...")
        for worker in self._workers:
            log.info(f"Starting {worker.thread_name}")
            t = threading.Thread(target = worker.worker, name=worker.thread_name)
            self._threads.append(t)
            t.start()

    async def process_shutdown(self, scope, event):
        log.info("Shutting down Workers...")
        for worker in self._workers:
            log.info(f"Sending Stop Signal to {worker.thread_name}")
            worker.shutdown.set()
        for thread in self._threads:
            log.info(f"Joining thread {worker.thread_name}")
            thread.join()