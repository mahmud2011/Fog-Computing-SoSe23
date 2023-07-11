from collections import deque
import datetime
import json
from math import sqrt
import os
import threading
import time
import requests
from websockets.sync.client import connect
from websockets.exceptions import ConnectionClosed
import stomp


from edge.config import Config

from .config import Config
from .worker import Worker
from .sensor import SensorManager

import logging

log = logging.getLogger(__name__)

class CloudConfigurationWebsocket(Worker):
    

    def __init__(self, thread_name: str, address: str, config: Config, sensormanager: SensorManager, cloudmanager) -> None:
        super().__init__(thread_name, config)

        self._addr = address.replace("http", "ws")

        self._sensormanager = sensormanager
        self._cloud_manager:CloudManager = cloudmanager

    def parse_config(data:str):
        return data

    def connect_and_subscribe(conn):
        conn.connect()
        conn.subscribe('/app/config', 0)

    class MyListener(stomp.ConnectionListener):
        def __init__(self, conn):
            self.conn = conn

        def on_error(self, frame):
            print('received an error "%s"' % frame.body)

        def on_message(self, frame):
            print('received a message "%s"' % frame.body)
            for x in range(10):
                print(x)
                time.sleep(1)
            print('processed message')

        def on_disconnected(self):
            print('disconnected')
            time.sleep(5)
            CloudConfigurationWebsocket.connect_and_subscribe(self.conn)

    def worker(self):
        log.debug(f"connecting to {self._addr}/topic/topic/config")
        conn = stomp.Connection([('192.168.178.111', 8080)], heartbeats=(4000, 4000), reconnect_attempts_max=1)
        conn.set_listener('', stomp.PrintingListener())
        CloudConfigurationWebsocket.connect_and_subscribe(conn)
        while True:
            if self.shutdown.is_set():
                conn.disconnect()
                log.debug("Shutdown Flag is set. Stopping...")
                return
            
        # with connect(f"{self._addr}/topic/config") as websocket:
        #     while (True):
        #         if self.shutdown.is_set():
        #             log.debug("Shutdown Flag is set. Stopping...")
        #             return
                
        #         try:
        #             data = websocket.recv(0)

        #             self._cloud_manager.connected_to_cloud()

        #             parsed_data = CloudConfigurationWebsocket.parse_config(data)

        #             self._sensormanager.sensor_config = parsed_data

        #             log.debug(parsed_data)


                    
        #         except ConnectionClosed:
        #             self._cloud_manager.is_alive()
        #         except:
        #             
        #             log.debug("Did not get a new websocket message")


class CloudDataQueue(Worker):
    
    class DequeEncoder(json.JSONEncoder):
        """
        code from https://stackoverflow.com/questions/56631350/how-to-send-a-deque-collection-via-flask-in-python
        """

        def default(self, obj):
            if isinstance(obj, deque):
                return list(obj)
            return json.JSONEncoder.default(self, obj)

    def __init__(self, thread_name: str, config: Config, address: str, cloudmanager) -> None:
        super().__init__(thread_name, config)

        self._addr = address

        self.datafile = os.path.join(self._config.data_path, 'data.json')

        self.datafilelock = threading.Lock()

        self._cloud_manager:CloudManager = cloudmanager
        

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
                file.write(json.dumps(self.dataqueue, cls=CloudDataQueue.DequeEncoder))
                file.close()

    def send_data_to_cloud(self, data):
        try:
            headers = {"Content-Type": "application/json"}
            to_send = {'data':data, 'token':self._cloud_manager._edge_id, 'id':None, 'message':""}
            requests.post(f"{self._addr}/api/edge-data", json=to_send, headers=headers)
            self._cloud_manager.connected_to_cloud()
            return True
        except:
            self._cloud_manager.is_alive()
            return False

    def get_data_from_cloud(self):
        try:
            headers = {"Content-Type": "application/json"}
            to_send = {'data':dict(), 'token':self._cloud_manager._edge_id, 'id':None, 'message':""}
            response: requests.Response = requests.get(f"{self._addr}/api/edge-data", json=to_send, headers=headers)
            print(response, response.content)
            return response.content.decode()
        except:
            self._cloud_manager.is_alive()
        

    def add_data(self, values: dict):
        with self.datafilelock:

            self.dataqueue.append(values)

            file = open(self.datafile, "w")
            file.write(json.dumps(self.dataqueue, cls=CloudDataQueue.DequeEncoder))
            file.close()
            
            log.debug("Saved data to File")

    def get_data(self):
        with self.datafilelock:

            return self.dataqueue[0]
        
    def confirm_sent_data(self):
        with self.datafilelock:

            data = self.dataqueue.popleft()
            file = open(self.datafile, "w")
            file.write(json.dumps(self.dataqueue, cls=CloudDataQueue.DequeEncoder))
            file.close()
            log.debug(f"Confirmed sending of {data}")


    def worker(self):
        # content = json.loads(self.get_data_from_cloud())

        # if content['data']['timestamp'] == self.get_data()['timestamp']:
        #     self.confirm_sent_data()

        while True:
            if self.shutdown.is_set():
                log.debug("Shutdown Flag is set. Stopping...")
                return
            
            log.info("Trying to send data in Buffer...")
            log.debug(f"Buffer: {self.dataqueue}")

            while len(self.dataqueue) > 0:
                data = self.get_data()
                if self.send_data_to_cloud(data):
                    self.confirm_sent_data()
                else:
                    break
            
            

            self.shutdown.wait(5)


class CloudManager(Worker):

    def __init__(self, thread_name: str, config: Config, sensors: SensorManager) -> None:
        super().__init__(thread_name, config)
        self._ip = self._config.cloud_ip
        self._port = self._config.cloud_port
        self._address = f'http://{self._ip}:{self._port}'

        self._dataqueuemanager = CloudDataQueue('data-queue', config, self._address, self)
        self._websocketmanager = CloudConfigurationWebsocket('config-websocket', self._address, config, sensors, self)
        self._workers_up = False

        self.last_connection = datetime.datetime.fromtimestamp(1)
        self.last_connection_lock = threading.Lock()
        self._alive = False
        self.exponential_backoff = 1

        self._edge_id = None
        self._edge_id_file = os.path.join(self._config.data_path, 'id')

        if os.path.exists(self._edge_id_file) and os.path.isfile(self._edge_id_file):
            file = open(self._edge_id_file, 'r')
            self._edge_id = file.read()
            file.close()
            log.info("Loaded id from file")

    def register(self):
        try:
            response: requests.Response = requests.get(f"{self._address}/api/register")
            self.connected_to_cloud()
            new_id = json.loads(response.content.decode())
            self._edge_id = new_id['token']
            with open(self._edge_id_file, 'x') as file:
                file.write(str(self._edge_id))
            log.info(f"Registered with cloud. ID: {self._edge_id}")
        except:
            log.info("Failed to register")


    def connected_to_cloud(self):
        with self.last_connection_lock:
            self.last_connection = datetime.datetime.now()

    def start_workers(self):
        if self._workers_up or self._edge_id == None:
            return
        log.info("Starting cloud workers...")
        self._dataqueuemanager.shutdown.clear()
        t = threading.Thread(target = self._dataqueuemanager.worker, name=self._dataqueuemanager.thread_name)
        t.start()
        # self._websocketmanager.shutdown.clear()
        # t = threading.Thread(target = self._websocketmanager.worker, name=self._websocketmanager.thread_name)
        # t.start()
        self._workers_up = True

    def shutdown_workers(self):
        if not self._workers_up:
            return
        log.info("shutting down cloud workers...")
        self._dataqueuemanager.shutdown.set()
        self._websocketmanager.shutdown.set()
        self._workers_up = False

    def is_alive(self):
        log.debug(f"Sending keepalive to {self._address}/api/edge-data")
        try:
            r = requests.get(f"{self._address}/api/edge-data", timeout=1)
            self.connected_to_cloud()
            if not self._alive:
                log.info(f"(Re)Connected to cloud at {self._address}")
                self._alive = True

                
        except:
            log.debug(
                f"Failed to connect when sending a request to {self._address}/api/edge-data")
            if self._alive:
                log.info(f"Failed to connect to cloud at {self._address}")
                self._alive = False
            
                

    def worker(self):
        while True:
            if self.shutdown.is_set():
                log.debug("Shutdown Flag is set. Stopping...")
                self._dataqueuemanager.shutdown.set()
                self._websocketmanager.shutdown.set()
                return

            if (datetime.datetime.now() - self.last_connection).total_seconds() > self._config.keepalive_interval:
                self.is_alive()

            if not self._alive and self.exponential_backoff < self._config.max_backoffs:
                self.exponential_backoff += 1

            if self._alive:
                self.exponential_backoff = 0

                if self._edge_id == None:
                    self.register()
                self.start_workers()

                self.shutdown.wait(self._config.keepalive_worker_interval)
            else:
                self.shutdown_workers()

                backoff_time = round(
                    (self._config.keepalive_worker_interval) * sqrt(self.exponential_backoff), 2)
                log.info(
                    f"Backing off for {backoff_time} seconds for cloud at {self._address}")
                self.shutdown.wait(backoff_time)