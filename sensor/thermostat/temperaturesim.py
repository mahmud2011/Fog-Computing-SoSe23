import logging
import threading
from .config import Config
from .simulators import Simulator

log = logging.getLogger(__name__)

class TemperatureSimulator(Simulator):

    # valve 0 => 16 degrees valve 100 => 25 degree

    WORKER_THREAD_NAME = "temperature-worker"

    def __init__(self, config:Config) -> None:
        super().__init__(config=config)

        self.thread_name = TemperatureSimulator.WORKER_THREAD_NAME

        self.templock = threading.Lock()
        self.temperature = 23.0

    @property
    def temperature(self):
        return self._temperature
    
    @temperature.setter
    def temperature(self, value):
        self._temperature:float = round(value, 2)

    def getsign(number: float, precision: int = 2):
        if round(number, precision) < 0:
            return -1
        elif round(number, precision) > 0:
            return 1
        else:
            return 0

    def setNewTemperature(self):
        with self.templock:
            targettemp = (((self._config.valve_open_value/100) * 9) + 16)
            diff = targettemp - self.temperature
            log.debug(f"Calculated differenz between {self.temperature} and the target of {targettemp}")
            if diff < 0.15 and diff > -0.15:
                tempchange = diff
                self.temperature = targettemp
            elif diff < 1 and diff > -1:
                tempchange = TemperatureSimulator.getsign(diff, 1) * 0.1
                self.temperature += tempchange
            else:
                tempchange = diff / 5
                self.temperature += tempchange

            log.info(f"Changed the temperature by {tempchange} to {self.temperature}")

    # Override
    def worker(self):
        while True:
            if self.shutdown.is_set():
                log.debug("Shutdown Flag is set. Stopping...")
                return
            
            self.setNewTemperature() 
            
            self.shutdown.wait(self._config.temperature_change_interval)