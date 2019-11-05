import asyncio
from typing import TYPE_CHECKING
from prompt_toolkit.keys import Keys
from IPython import embed
from lft.event.mediators import DelayedEventMediator
from lft.event.mediators.delayed_event_mediator import (DelayedEventInstantMediatorExecutor,
                                                        DelayedEventRecorderMediatorExecutor)

if TYPE_CHECKING:
    from lft.app import App


class Console:
    def run(self, app: 'App'):
        loop = asyncio.get_event_loop()
        start_time = loop.time()

        try:
            embed(colors='Neutral')
        finally:
            for node in app.nodes:
                mediator = node.event_system.get_mediator(DelayedEventMediator)
                self._restore_delayed_mediator(start_time, mediator)

    def _restore_delayed_mediator(self,
                                  start_time: float,
                                  mediator: DelayedEventMediator):
        executor = mediator._executor
        if (not isinstance(executor, DelayedEventInstantMediatorExecutor) and
                not isinstance(executor, DelayedEventRecorderMediatorExecutor)):
            return

        old_handlers = executor.handlers
        executor.handlers = set()

        for old_handler in old_handlers:
            old_handler.timer_handler.cancel()
            diff = old_handler.timer_handler.when() - start_time
            mediator.execute(diff, old_handler.event)
