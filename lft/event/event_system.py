import asyncio
import logging
from typing import Dict, Type, IO, Optional
from lft.event import EventSimulator, EventRecorder, EventReplayer, EventMediator

__all__ = ("EventSystem", )


class EventSystem:
    def __init__(self, logger: Optional[logging.Logger] = None, use_priority=True):
        self.simulator = EventSimulator(logger, use_priority)
        self.recorder = EventRecorder(self.simulator)
        self.replayer = EventReplayer(self.simulator)
        self.mediators: Dict[Type[EventMediator], EventMediator] = {}

    def start_record(self,
                     record_io: IO, mediator_ios: Dict[Type[EventMediator], IO]=None,
                     blocking=True, loop: asyncio.AbstractEventLoop=None):
        if not mediator_ios:
            mediator_ios = {}
        for mediator in self.mediators.values():
            io = mediator_ios.get(type(mediator))
            if io:
                mediator.switch_recorder(self.recorder, io=io)
            else:
                mediator.switch_recorder(self.recorder)
        self.recorder.start(record_io)
        return self.simulator.start(blocking, loop)

    def start_replay(self,
                     record_io: IO, mediator_ios: Dict[Type[EventMediator], IO]=None,
                     blocking=True, loop: asyncio.AbstractEventLoop=None):
        if not mediator_ios:
            mediator_ios = {}
        for mediator in self.mediators.values():
            io = mediator_ios.get(type(mediator))
            if io:
                mediator.switch_replayer(self.replayer, io=io)
            else:
                mediator.switch_replayer(self.replayer)
        self.replayer.start(record_io)
        return self.simulator.start(blocking, loop)

    def start(self, blocking=True, loop: asyncio.AbstractEventLoop=None):
        for mediator in self.mediators.values():
            mediator.switch_instant(self.simulator)
        return self.simulator.start(blocking, loop)

    def stop(self):
        self.simulator.stop()
        self.recorder.stop()
        self.replayer.stop()

    def close(self):
        self.simulator.clear()
        self.recorder.close()
        self.replayer.close()

    def set_mediator(self, mediator_type: Type[EventMediator]):
        self.mediators[mediator_type] = mediator_type()

    def get_mediator(self, mediator_type: Type[EventMediator]):
        return self.mediators[mediator_type]

    def del_mediator(self, mediator_type: Type[EventMediator]):
        del self.mediators[mediator_type]
