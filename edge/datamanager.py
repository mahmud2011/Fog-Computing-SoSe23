import datetime
import json
import time
import requests
from .config import Config
from .worker import Worker
from .sensor import SensorManager
from .cloud import CloudDataQueue

import logging

log = logging.getLogger(__name__)


class DataManger(Worker):
    
    def __init__(self, thread_name: str, config: Config, sensormanager: SensorManager, dataqueue: CloudDataQueue) -> None:
        super().__init__(thread_name, config)

        self._sensor_manager = sensormanager
        self._data_queue = dataqueue

    def worker(self):
        while True:
            if self.shutdown.is_set():
                return
            
            # collect data from all sensors 
            log.debug("Collecting data from sensors")
            data = {'timestamp': time.mktime(datetime.datetime.now().timetuple())}
            for sensor in self._sensor_manager.sensors:
                if not sensor._alive:
                    continue
                response: requests.Response = sensor.request_data()
                if response == None:
                    continue
                log.debug(f"Received {response.content} with {response.status_code}")
                data.update({f"{sensor._type[0]}-{sensor._address}":json.loads(response.content.decode())})

            log.debug(f"data from {data['timestamp']}:\n{data}")

            # send to CloudDataQueue

            if len(data) > 1:
                self._data_queue.add_data(data)


            self.shutdown.wait(self._config.sensor_query_interval)