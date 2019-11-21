import asyncio
import IPython
from typing import TYPE_CHECKING
from lft.event.mediators import DelayedEventMediator
from lft.event.mediators.delayed_event_mediator import (DelayedEventInstantMediatorExecutor,
                                                        DelayedEventRecorderMediatorExecutor)

if TYPE_CHECKING:
    from lft.app import App
    from lft.app.node import Node


class Console:
    def run(self, app: 'App'):
        nodes = app.nodes
        user_ns = {"nodes": nodes}
        for i, node in enumerate(nodes):
            debug_patch(node)
            user_ns[f"node{i}"] = node

        loop = asyncio.get_event_loop()
        start_time = loop.time()

        try:
            IPython.start_ipython(argv=[], user_ns=user_ns)
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


def debug_patch(node: 'Node'):
    node.pause = lambda: node.event_system.stop()
    node.resume = lambda: node.event_system.start(False)

    node.order_layer = node._consensus._order_layer
    node.sync_layer = node._consensus._sync_layer
    node.round_layer = node._consensus._round_layer

    node.order_layer.term = node.order_layer._term
    node.sync_layer.term = node.sync_layer._term
    node.round_layer.term = node.round_layer._term
