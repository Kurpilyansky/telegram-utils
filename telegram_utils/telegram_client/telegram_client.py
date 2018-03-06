import os
import time
import sys
import re
import json
import socket
import subprocess


# TODO move to another place
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TelegramClient:
    def __init__(self, port, verbose=False):
        self._socket = None
        self._process = None
        self._client_started = False
        self._port = port
        self._verbose = verbose

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    class TryAgainError(Exception):
        pass

    def make_request(self, request):
        return self.make_complex_request(lambda make: make(request))

    def make_complex_request(self, request_func):
        for attempt in range(100):
            try:
                return request_func(self._try_make_request)
            except self.TryAgainError:
                time.sleep(60.0)
        raise AssertionError('Can not receive answer from TelegramClient')

    def close(self):
        self._stop_client()

    def _try_make_request(self, request):
        self._ensure_start()
        if self._verbose:
            sys.stderr.write(request + '\n')
        self._socket.send((request + '\n').encode())
        self._socket.settimeout(2.0)
        try:
            response = self._socket.recv(60000)
        except socket.timeout:
            self._stop_client()
            raise self.TryAgainError()
        response = response.decode()
        if self._verbose:
            sys.stderr.write(response + '\n')
        match = re.match('ANSWER (\d+)\n(.*)', response)
        if bool(match):
            return json.loads(match.group(2))
        return None

    def _ensure_start(self):
        if not self._client_started:
            path = os.path.join(BASE_DIR, 'tg/bin/telegram-cli')
            self._process = subprocess.Popen([path, '-I', '-W', '--json', '-P %d' % self._port],
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.PIPE)
            time.sleep(1.0)
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.connect(('localhost', self._port))
            self._client_started = True

    def _stop_client(self):
        if self._client_started:
            if self._socket:
                self._socket.close()
                self._socket = None
            if self._process:
                self._process.kill()
                self._process.wait()
                self._process = None
            self._client_started = False

            ################
            # to fix console state: https://stackoverflow.com/questions/7938402/terminal-in-broken-state-invisible-text-no-echo-after-exit-during-input
            os.system('stty sane')
            ################

