import logging
from random import randint
import threading
from time import sleep
import falcon.asgi
import uvicorn
import asyncio

from .config import Config

from .temperaturesim import TemperatureSimulator
from .edge import EdgeContext

from .endpoints.configuration import ConfigurationEndpoint
from .endpoints.data import DataEndpoint
from .endpoints.alive import AliveEndpoint

log = logging.getLogger(__name__)


restart_stop = threading.Event()


class WorkerManager:

    def __init__(self, config, simulators:list) -> None:
        self._config = config
        self._sims = simulators

    async def process_startup(self, scope, event):
        log.info("Starting Up Workers...")
        for sim in self._sims:
            log.info(f"Starting {sim.thread_name}")
            t = threading.Thread(target = sim.worker, name=sim.thread_name)
            t.start()

    async def process_shutdown(self, scope, event):
        log.info("Shutting down Workers...")
        for sim in self._sims:
            log.info(f"Stopping {sim.thread_name}")
            sim.shutdown.set()

def create_app(config=None):

    config = config or Config()

    edgecontext = EdgeContext(config=config)

    tempsim = TemperatureSimulator(config)

    app = falcon.asgi.App(
        middleware = [WorkerManager(config, [tempsim, edgecontext])]
    )

    config_endpoint = ConfigurationEndpoint(config=config, edge=edgecontext)
    data_endpoint = DataEndpoint(config, tempsim, edge=edgecontext)
    alive_endpoint = AliveEndpoint(edge=edgecontext)

    app.add_route('/configuration', config_endpoint)
    app.add_route("/configuration/valve", config_endpoint, suffix="valve")
    # curl -X POST 127.0.0.1:8000/configuration/valve -H 'Content-Type: application/json' -d '{"valve":50}'

    app.add_route("/data", data_endpoint)

    app.add_route("/alive", alive_endpoint)

    uvicorn_config = uvicorn.Config(app=app, host=None, port=config.server_port, log_level=config.logging_level.lower())
    uvicorn_server = uvicorn.Server(uvicorn_config)

    asyncio.run(uvicorn_server.serve())

if __name__ == "__main__":
    create_app()
