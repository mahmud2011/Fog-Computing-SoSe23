import logging
import traceback
from ..config import Config
from ..edge import EdgeContext
from falcon import Response, Request
import falcon
import json
import jsonpickle

log = logging.getLogger(__name__)

class ConfigurationEndpoint:

    def __init__(self, config: Config, edge: EdgeContext) -> None:
        self._config = config
        self._edge = edge
    
    async def on_get(self, req:Request, resp:Response):
        self._edge.edge_seen()
        resp.content_type = falcon.MEDIA_JSON
        resp.status = falcon.HTTP_200
        resp.media = json.dumps(jsonpickle.encode(self._config, unpicklable=False), indent=2)

    async def on_get_valve(self, req:Request, resp:Response):
        self._edge.edge_seen()
        resp.content_type = falcon.MEDIA_JSON
        resp.status = falcon.HTTP_200
        resp.media = json.dumps(self._config.valve_open_value)

    async def on_post_valve(self, req:Request, resp:Response):
        self._edge.edge_seen()
        try:
            json_media = await req.media
            if not 'valve' in json_media.keys():
                raise KeyError
            self._config.valve_open_value = json_media['valve']
            resp.content_type = falcon.MEDIA_JSON
            resp.status = falcon.HTTP_200
        except KeyError as e:
            resp.status = falcon.HTTP_400
            log.error("Key Error when trying to post data")
            traceback.print_exc()
        except ValueError as e:
            resp.status = falcon.HTTP_400
            log.error("Value Error when trying to post data")
            traceback.print_exc()
        
        