import os
import pathlib
import threading
import logging

log = logging.getLogger(__name__)

class Config:

    DEFAULT_LOGGING_FORMAT = r"%(asctime)s - %(filename)s - %(funcName)s - %(threadName)s - %(message)s"

    DEFAULT_DATA_LOCATION = os.path.normpath(os.path.join(os.getcwd(), 'data'))

    DEFAULT_BUFFER_LENGTH = 20

    DEFAULT_TEMPCHANGE_INTERVAL = 1

    DEFAULT_LOGGING_LEVEL = "DEBUG"

    DEFAULT_EDGE_TIMEOUT = 60

    DEFAULT_SERVER_PORT = 24241

    DEFAULT_VALVE_VALUE = 50

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

        

        self.logging_level = os.environ.get("THERMOSTAT_LOGGING_LEVEL", self.DEFAULT_LOGGING_LEVEL)
        Config.__setup_logging__(self.logging_level)

        log.info(f"logging level: {self.logging_level}")

        self.crash: bool = False
        self.death: bool = False

        self.server_port = int(os.environ.get("THERMOSTAT_SERVER_PORT", self.DEFAULT_SERVER_PORT))

        self.multicast_port = int(os.environ.get("THERMOSTAT_MULTICAST_PORT", self.DEFAULT_MULTICAST_PORT))

        

        self.data_path = pathlib.Path(os.environ.get("THERMOSTAT_DATA_LOCATION", self.DEFAULT_DATA_LOCATION))
        self.data_path.mkdir(parents=True, exist_ok=True)

        log.info(f"data path: {self.data_path}")

        # self.buffer_maxlen = os.environ.get("THERMOSTAT_BUFFER_LENGTH", self.DEFAULT_BUFFER_LENGTH)

        # log.info(f"buffer length: {self.buffer_maxlen}")

        self.temperature_change_interval = os.environ.get("THERMOSTAT_TEMPERATURE_CHANGE_INTERVAL", self.DEFAULT_TEMPCHANGE_INTERVAL)

        log.info(f"sensing interval: {self.temperature_change_interval}")

        self.valve_open_value = os.environ.get("THERMOSTAT_VALVE_DEFAULT_VALUE", self.DEFAULT_VALVE_VALUE)

        self.edge_search_timer = os.environ.get("THERMOSTAT_EDGE_TIMEOUT", self.DEFAULT_EDGE_TIMEOUT)


        self.datafile = os.path.join(self.data_path, 'config.settings')

        #PERSIST SETTINGS

        

    @property
    def valve_open_value(self):
        with self.configlock:
            return self._valve_open_value
    
    @valve_open_value.setter
    def valve_open_value(self, value:int):
        with self.configlock:
            if value > 100:
                log.error("Tried to open valve more than allowed")
                raise ValueError("Valve cant be opened above 100%")
            if value < 0:
                log.error("Tried to close valve more than allowed")
                raise ValueError("Valve cant be closed less than 0%")
            self._valve_open_value = value