from edge.config import Config
from .worker import Worker

class CloudManager(Worker):

    def __init__(self, thread_name: str, config: Config, ip:str, port:int) -> None:
        super().__init__(thread_name, config)
        self._ip = ip
        self._port = port

    