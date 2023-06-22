import os
import pathlib

import logging

log = logging.getLogger(__name__)

class Config:

    DEFAULT_LOGGING_FORMAT = r"%(asctime)s - %(filename)s - %(funcName)s - %(threadName)s - %(message)s"

    DEFAULT_DATA_LOCATION = os.path.normpath(os.path.join(os.getcwd(), 'data'))

    DEFAULT_BUFFER_LENGTH = 20

    DEFAULT_LOGGING_LEVEL = "DEBUG"


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
        self.logging_level = os.environ.get("THERMOSTAT_LOGGING_LEVEL", self.DEFAULT_LOGGING_LEVEL)
        Config.__setup_logging__(self.logging_level)

        log.info(f"logging level: {self.logging_level}")

        self.data_path = pathlib.Path(os.environ.get("THERMOSTAT_DATA_LOCATION", self.DEFAULT_DATA_LOCATION))
        self.data_path.mkdir(parents=True, exist_ok=True)

        log.info(f"data path: {self.data_path}")

        self.buffer_maxlen = os.environ.get("THERMOSTAT_BUFFER_LENGTH", self.DEFAULT_BUFFER_LENGTH)

        log.info(f"buffer length: {self.buffer_maxlen}")

        

