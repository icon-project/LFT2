import aiohttp
import base64
import os
import pickle
from jsonrpcclient.clients.http_client import HTTPClient
from jsonrpcclient.clients.aiohttp_client import AiohttpClient
from typing import IO
from lft.event import EventMediation, EventInstantMediationExecutor, EventRecorder, EventReplayer
from lft.event import EventReplayerMediationExecutor, EventRecorderMediationExecutor


class JsonRpcEventInstantMediationExecutor(EventInstantMediationExecutor):
    def execute(self, url: str, method: str, params: dict=None):
        return request(url, method, **params)

    async def execute_async(self, url: str, method: str, params: dict=None):
        return await request_async(url, method, **params)


class JsonRpcEventRecorderMediationExecutor(EventRecorderMediationExecutor):
    def __init__(self, event_recorder: EventRecorder, io: IO):
        super().__init__(event_recorder)
        self._io = io
        self._number = -1
        self._started = False

    def execute(self, url: str, method: str, params: dict=None):
        result = ""
        try:
            result = request(url, method, params)
        except Exception as e:
            result = e
        finally:
            self._write(result)
            if isinstance(result, Exception):
                raise result
            else:
                return result

    async def execute_async(self, url: str, method: str, params: dict=None):
        result = ""
        try:
            result = await request_async(url, method, params)
        except Exception as e:
            result = e
        finally:
            self._write(result)
            if isinstance(result, Exception):
                raise result
            else:
                return result

    def _write(self, result):
        if self._number != self._event_recorder.number:
            self._number = self._event_recorder.number

            if self._started:
                self._io.write(os.linesep)
            self._io.write("#")
            self._io.write(str(self._number))
            self._io.write(os.linesep)
        self._io.write("$")
        dumped = base64.encodebytes(pickle.dumps(result)).decode()
        dumped_len = len(dumped)
        self._io.write(str(dumped_len))
        self._io.write(os.linesep)
        self._io.write(dumped)
        self._io.write(os.linesep)
        self._started = True

        if isinstance(result, Exception):
            raise result
        else:
            return result


class JsonRpcEventReplayerMediationExecutor(EventReplayerMediationExecutor):
    def __init__(self, event_replayer: EventReplayer, io: IO):
        super().__init__(event_replayer)
        self._io = io
        self._number = -1

    def execute(self, url: str, method: str, params: dict=None):
        number = self._number
        while number < self._event_replayer.number:
            line = self._io.readline()
            if not line:
                continue
            if line[0] != "#":
                continue
            number = int(line[1:])

        if number != self._event_replayer.number:
            raise RuntimeError

        self._number = number
        line = self._io.readline()
        if line[0] != "$":
            raise RuntimeError

        pickled_len = int(line[1:])
        response_pickled = self._io.read(pickled_len + 1)
        response_pickled = response_pickled.encode()
        response_pickled = base64.decodebytes(response_pickled)
        result = pickle.loads(response_pickled)
        if isinstance(result, Exception):
            raise result
        else:
            return result

    async def execute_async(self, url: str, method: str, params: dict=None):
        return self.execute(url, method, params)


class JsonRpcEventMediation(EventMediation):
    InstantExecutorType = JsonRpcEventInstantMediationExecutor
    RecorderExecutorType = JsonRpcEventRecorderMediationExecutor
    ReplayerExecutorType = JsonRpcEventReplayerMediationExecutor

    def execute(self, url: str, method: str, params: dict=None):
        return super().execute(url=url, method=method, params=params)

    async def execute_async(self, url: str, method: str, params: dict=None):
        return await super().execute_async(url=url, method=method, params=params)


def request(url: str, method: str, params: dict=None):
    if not params:
        params = {}
    client = HTTPClient(url)
    return client.request(method, **params)


async def request_async(url: str, method: str, params: dict=None):
    if not params:
        params = {}

    async with aiohttp.ClientSession() as session:
        client = AiohttpClient(session, url)
        response = await client.request(method, **params)
        return response.data.result
