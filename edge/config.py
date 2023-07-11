import logging
import os
import pathlib
import threading

log = logging.getLogger(__name__)

class Config:

    DEFAULT_LOGGING_FORMAT = r"%(asctime)s - %(filename)s - %(funcName)s - %(threadName)s - %(message)s"
    DEFAULT_LOGGING_LEVEL = "DEBUG"

    DEFAULT_SENSING_INTERVAL = 3
    
    DEFAULT_PUSH_INTERVAL = 5

    DEFAULT_KEEPALIVE_INTERVAL = 20

    DEFAULT_KEEPALIVE_WORKER_INTERVAL = 5

    DEFAULT_MAX_BACKOFFS = 4

    DEFAULT_EXPONENTIAL_BACKOFF = True

    DEFAULT_SERVER_PORT = 8000

    DEFAULT_MULTICAST_PORT = 5924

    DEFAULT_QUERY_INTERVAL = 5

    DEFAULT_DATA_LOCATION = "data"

    DEFAULT_DATA_BUFFER_LENGTH = 20

    DEFAULT_CLOUD_IP = "192.168.178.111"

    DEFAULT_CLOUD_PORT = 8080


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

        self.data_path = pathlib.Path(os.environ.get("EDGE_DATA_LOCATION", self.DEFAULT_DATA_LOCATION))
        self.data_path.mkdir(parents=True, exist_ok=True)

        self.server_port = int(os.environ.get("EDGE_SERVER_PORT", self.DEFAULT_SERVER_PORT))

        self.multicast_port = int(os.environ.get("EDGE_MULTICAST_PORT", self.DEFAULT_MULTICAST_PORT))

        self.cloud_ip = os.environ.get("EDGE_CLOUD_IP", self.DEFAULT_CLOUD_IP)

        self.cloud_port = os.environ.get("EDGE_CLOUD_PORT", self.DEFAULT_CLOUD_PORT)


        self.keepalive_interval = int(os.environ.get("EDGE_KEEPALIVE_INTERVAL", self.DEFAULT_KEEPALIVE_INTERVAL))

        self.keepalive_worker_interval = int(os.environ.get("EDGE_KEEPALIVE_WORKER_INTERVAL", self.DEFAULT_KEEPALIVE_WORKER_INTERVAL))

        self.max_backoffs = int(os.environ.get("EDGE_MAX_BACKOFFS", self.DEFAULT_MAX_BACKOFFS))


        self.sensor_query_interval = int(os.environ.get("EDGE_QUERY_INTERVAL", self.DEFAULT_QUERY_INTERVAL))

        self.buffer_maxlen = int(os.environ.get("EDGE_DATA_BUFFER_LENGTH", self.DEFAULT_DATA_BUFFER_LENGTH))