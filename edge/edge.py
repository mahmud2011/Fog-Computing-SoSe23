import logging
from .config import Config
from .workermanager import WorkerManager
from .sensormanager import SensorManager

import falcon.asgi
import uvicorn
import asyncio

log = logging.getLogger(__name__)

def create_app(config:Config=None):
    
    config = config or Config()

    sensor_manager = SensorManager("sensor-manager", config=config)

    app = falcon.asgi.App(
        middleware = [WorkerManager(config, [sensor_manager])]
    )

    uvicorn_config = uvicorn.Config(app=app, host=None, port=config.server_port, log_level=config.logging_level.lower())
    uvicorn_server = uvicorn.Server(uvicorn_config)

    asyncio.run(uvicorn_server.serve())

    exit(0)

if __name__ == "__main__":
    create_app()