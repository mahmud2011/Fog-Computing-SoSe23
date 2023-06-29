from falcon import Response, Request
import falcon

class AliveEndpoint():

    async def on_get(self, req:Request, resp:Response):
        resp.status = falcon.HTTP_200