import asyncio
from typing import Dict, Type, IO
from lft.event import EventSimulator, EventRecorder, EventReplayer, EventMediation


class EventSystem:
    def __init__(self):
        self.simulator = EventSimulator()
        self.recorder = EventRecorder(self.simulator)
        self.replayer = EventReplayer(self.simulator)
        self.mediations: Dict[Type[EventMediation], EventMediation] = {}

    def start_record(self,
                     record_io: IO, mediation_ios: Dict[Type[EventMediation], IO],
                     blocking=True, loop: asyncio.AbstractEventLoop=None):
        for mediation in self.mediations.values():
            io = mediation_ios.get(type(mediation))
            if io:
                mediation.switch_recorder(self.recorder, io=io)
            else:
                mediation.switch_recorder(self.recorder)
        self.recorder.start(record_io)
        self.simulator.start(blocking, loop)

    def start_replay(self,
                     record_io: IO, mediation_ios: Dict[Type[EventMediation], IO],
                     blocking=True, loop: asyncio.AbstractEventLoop=None):
        for mediation in self.mediations.values():
            io = mediation_ios.get(type(mediation))
            if io:
                mediation.switch_replayer(self.replayer, io=io)
            else:
                mediation.switch_replayer(self.replayer)
        self.replayer.start(record_io)
        self.simulator.start(blocking, loop)

    def start(self, blocking=True, loop: asyncio.AbstractEventLoop=None):
        self.simulator.start(blocking, loop)

    def stop(self):
        self.simulator.stop()
        self.recorder.stop()
        self.replayer.stop()

    def close(self):
        self.simulator.clear()
        self.recorder.close()
        self.replayer.close()

    def set_mediation(self, mediation_type: Type[EventMediation]):
        self.mediations[mediation_type] = mediation_type()

    def get_mediation(self, mediation_type: Type[EventMediation]):
        return self.mediations[mediation_type]

    def del_mediation(self, mediation_type: Type[EventMediation]):
        del self.mediations[mediation_type]
