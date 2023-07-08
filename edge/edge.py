import logging
from random import randint
from time import sleep
from .config import Config
from .workermanager import WorkerManager
from .sensor import SensorManager
from .datamanager import DataManger
from .cloud import CloudManager

import falcon.asgi
import uvicorn
import asyncio

log = logging.getLogger(__name__)

def create_app(config:Config=None):
    
    config = config or Config()

    sensor_manager = SensorManager("sensor-manager", config=config)
    cloud_manager = CloudManager('cloud-manager', config, sensor_manager)
    data_manager = DataManger("data-manager", config=config, sensormanager=sensor_manager, dataqueue=cloud_manager._dataqueuemanager)
    


    app = falcon.asgi.App(
        middleware = [WorkerManager(config, [sensor_manager, data_manager, cloud_manager])]
    )

    uvicorn_config = uvicorn.Config(app=app, host=None, port=config.server_port, log_level=config.logging_level.lower())
    uvicorn_server = uvicorn.Server(uvicorn_config)

    asyncio.run(uvicorn_server.serve())

if __name__ == "__main__":
    create_app()