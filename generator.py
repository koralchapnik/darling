import socket
import time

from experiments.configurations_map import config
from experiments.consts import *
from parsers.parser import Parser


class EventsGenerator:
    def __init__(self):
        self.boost = self.get_boost(config[BOOST])
        self.random_indexes = list(self.boost.keys())
        self.sleep_reg = float(os.getenv('SLEEP_REG'))
        self.sleep_load = float(os.getenv('SLEEP_LOAD'))
        self.config = config
        self.parser = Parser(self.config[EVENT_TYPES])
        self.types, self.pattern = self.parser.parse_pattern(self.config[PATTERN],
                                                             self.config.get(SELECTIVITY),
                                                             self.config[
                                                                 ATTRS_DIST_PARAMS], config[ATTRS_TYPES])
        filename, self.types_names = Parser.get_data_filename(DATASET_KIND,
                                                              config[PATTERN])
        print(self.types_names)
        self.file = f'{ORIGIN_DATA_DIR}/{filename}'

    def get_boost(self, boost_percents):
        """
        Creates boost in indexes from boost given in percents
        """
        new_boost = {}
        for (index, val) in boost_percents.items():
            new_index = int(DATA_SIZE * index / 100)
            new_val = int(DATA_SIZE * val / 100)
            new_boost[new_index] = new_val
        print(f'boost:\n{new_boost}')
        return new_boost

    def check_warm_up_state(self, client_socket) -> bool:
        client_socket.send(CHECK_FINISHED_WARM_UP.encode())
        ack = client_socket.recv(1024).decode()
        if ack == FINISHED_WARM_UP:
            return True
        elif ack == NOT_FINISHED_WARM_UP:
            return False
        else:
            print(f'wrong return value for check finished warm up! {ack}')
            return False

    def send_events(self, time_diffs_file: str = None):
        client_socket = socket.socket()  # instantiate
        client_socket.connect((IP, PORT))  # connect to the server
        x = client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        sleep = False
        finished_warm_up = False
        boost_count = None
        print(f'warm up size: {WARM_UP}')
        time_diffs = []
        if time_diffs_file is not None:
            with open(time_diffs_file, 'r') as t:
                for l in t:
                    time_diffs.append(float(l.rstrip()))
        try:
            with open(self.file, 'r') as f:
                for i, line in enumerate(f):
                    if i == DATA_SIZE:
                        break
                    if i % 1000 == 0:
                        print(f'added {i} events')
                    if line.split(',')[0] not in self.types_names:
                        continue
                    if i == WARM_UP:
                        sleep = True
                        while not finished_warm_up:
                            finished_warm_up = self.check_warm_up_state(
                                client_socket)
                            if not finished_warm_up:
                                time.sleep(SLEEP_WARM_UP_SEC)
                    if sleep:
                        time_sleep = 0 if time_diffs_file is None else \
                            time_diffs[i]
                        if i in self.random_indexes:
                            boost_count = self.boost[i]
                            self.random_indexes.remove(i)
                        if not boost_count:
                            time.sleep(self.sleep_reg + time_sleep)
                        else:
                            time.sleep(self.sleep_load + time_sleep)
                            boost_count -= 1
                    line = line.strip('\n')
                    splitted_line = line.split(',')
                    if os.environ.get('WS', None) is not None:
                        event, ws = ','.join(splitted_line[:-1]), splitted_line[
                            -1]
                    else:
                        event, ws = ','.join(splitted_line), '0'
                    payload = f'{event}{SEPARATOR}{ws}'.encode()
                    sent = False
                    while not sent:
                        try:
                            client_socket.send(payload)
                            ack = client_socket.recv(1024).decode()
                            if ack == GOT_MESSAGE:
                                sent = True
                        except socket.error:
                            # set connection status and recreate socket
                            connected = False
                            clientSocket = socket.socket()
                            print("connection lost... reconnecting")
                            while not connected:
                                # attempt to reconnect, otherwise sleep for 2 seconds
                                try:
                                    clientSocket.connect((IP, PORT))
                                    connected = True
                                    print("re-connection successful")
                                except socket.error:
                                    sleep(2)

            client_socket.send(FINISH.encode())
        finally:
            client_socket.close()


if __name__ == '__main__':
    time.sleep(5)  # sleeping until the server up
    time_diffs_file = os.environ.get('ARRIVAL_RATES', None)
    EventsGenerator().send_events(time_diffs_file)
