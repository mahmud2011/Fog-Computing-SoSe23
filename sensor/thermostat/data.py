from collections import deque
import logging
from .config import Config

import datetime
import os
import json
import threading

log = logging.getLogger(__name__)


class Data:

    class DequeEncoder(json.JSONEncoder):
        """
        code from https://stackoverflow.com/questions/56631350/how-to-send-a-deque-collection-via-flask-in-python
        """

        def default(self, obj):
            if isinstance(obj, deque):
                return list(obj)
            return json.JSONEncoder.default(self, obj)

    def __init__(self, config: Config = None) -> None:
        self._config = config

        self.datafile = os.path.join(self._config.data_path, 'data.json')

        self.datafilelock = threading.Lock()

        with self.datafilelock:

            if os.path.exists(self.datafile) and os.path.isfile(self.datafile):
                file = open(self.datafile, "r")
                datalist = json.loads(file.read())
                self.dataqueue = deque(
                    datalist, maxlen=self._config.buffer_maxlen)
                file.close
            else:
                self.dataqueue = deque(maxlen=self._config.buffer_maxlen)
                file = open(self.datafile, "x")
                file.write(json.dumps(self.dataqueue, cls=Data.DequeEncoder))
                file.close()

    def add_data(self, time: datetime.datetime, values: dict):
        """
        `dict` should be a dict with `{sensor:value}`
        """
        new_data = {'time': time.isoformat()}
        new_data.update(values)

        with self.datafilelock:

            self.dataqueue.append(new_data)

            file = open(self.datafile, "w")
            file.write(json.dumps(self.dataqueue, cls=Data.DequeEncoder))
            file.close()
            
            log.debug("Saved data to File")
