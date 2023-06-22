import datetime
import logging
import threading
import falcon.asgi

from .config import Config
from .data import Data

from .temperaturesim import TemperatureSimulator

log = logging.getLogger(__name__)


class SimulatorMiddleware:

    def __init__(self, config, simulators:list) -> None:
        self._config = config
        self._sims = simulators

    async def process_startup(self, scope, event):
        log.info("Starting Up Sensor Simulators...")
        for sim in self._sims:
            t = threading.Thread(target = sim.worker, name=sim.thread_name)
            t.start()

    async def process_shutdown(self, scope, event):
        log.info("Shutting down Sensor Simulators...")
        for sim in self._sims:
            sim.shutdown.set()

def create_app(config=None):

    config = config or Config()
    data = Data(config)

    tempsim = TemperatureSimulator(config, data)



    app = falcon.asgi.App(
        middleware = [SimulatorMiddleware(config, [tempsim])]
    )

    return app