import logging
import os
import threading

log = logging.getLogger(__name__)

class Config:

    DEFAULT_LOGGING_FORMAT = r"%(asctime)s - %(filename)s - %(funcName)s - %(threadName)s - %(message)s"
    DEFAULT_LOGGING_LEVEL = "DEBUG"

    DEFAULT_SENSING_INTERVAL = 3
    
    DEFAULT_PUSH_INTERVAL = 5

    DEFAULT_EXPONENTIAL_BACKOFF = True

    DEFAULT_SERVER_PORT = 8000

    DEFAULT_MULTICAST_PORT = 5924

    def __setup_logging__(logging_level:str):
        level = logging.INFO
        if logging_level == "DEBUG":
            level = logging.DEBUG
        elif logging_level == "WARNING":
            level = logging.WARNING
        elif logging_level == "ERROR":
            level = logging.ERROR
        elif logging_level == "CRITICAL":
            level = logging.CRITICAL

        logging.basicConfig(level=level, format=Config.DEFAULT_LOGGING_FORMAT)

    def __init__(self) -> None:
        self.configlock = threading.Lock()

        self.logging_level = os.environ.get("EDGE_LOGGING_LEVEL", self.DEFAULT_LOGGING_LEVEL)
        Config.__setup_logging__(self.logging_level)

        self.server_port = int(os.environ.get("EDGE_SERVER_PORT", self.DEFAULT_SERVER_PORT))

        self.multicast_port = int(os.environ.get("EDGE_MULTICAST_PORT", self.DEFAULT_MULTICAST_PORT))