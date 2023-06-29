import datetime
import logging
import threading
import falcon.asgi

from .config import Config
from .data import Data

from .temperaturesim import TemperatureSimulator

from .endpoints.configuration import ConfigurationEndpoint
from .endpoints.data import DataEndpoint
from .endpoints.alive import AliveEndpoint

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
    #data = Data(config)

    tempsim = TemperatureSimulator(config)



    app = falcon.asgi.App(
        middleware = [SimulatorMiddleware(config, [tempsim])]
    )

    config_endpoint = ConfigurationEndpoint(config=config)
    data_endpoint = DataEndpoint(config, tempsim)
    alive_endpoint = AliveEndpoint()

    app.add_route('/configuration', config_endpoint)
    app.add_route("/configuration/valve", config_endpoint, suffix="valve")
    # curl -X POST 127.0.0.1:8000/configuration/valve -H 'Content-Type: application/json' -d '{"valve":50}'

    app.add_route("/data", data_endpoint)

    app.add_route("/alive", alive_endpoint)

    return app