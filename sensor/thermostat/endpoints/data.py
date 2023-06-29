import logging
from ..temperaturesim import TemperatureSimulator
from ..config import Config
from falcon import Response, Request
import falcon
import json
import jsonpickle


log = logging.getLogger(__name__)

class DataEndpoint:

    def __init__(self, config: Config, data: TemperatureSimulator) -> None:
        self._config = config
        self._data = data

    async def on_get(self, req:Request, resp:Response):
        try:
            with self._data.templock:
                data = {'temperature':self._data.temperature}
            resp.media = data
            resp.content_type = falcon.MEDIA_JSON
            resp.status = falcon.HTTP_200
        except:
            pass