import sys
from falcon import Response, Request
import falcon
from ..edge import EdgeContext
from ..config import Config


class AliveEndpoint():

    def __init__(self, edge: EdgeContext) -> None:
        self._edge = edge

    async def on_get(self, req:Request, resp:Response):
        self._edge.edge_seen()
        resp.status = falcon.HTTP_200