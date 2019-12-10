from unittest.mock import MagicMock, AsyncMock

from lft.consensus.epoch import Epoch
from lft.consensus.round import Round


class RoundMock(Round):
    def __init__(self, epoch: Epoch, round_num: int):
        self._epoch = epoch
        self._num = round_num

        self._election = MagicMock()
        self._messages = MagicMock()

        self._election = MagicMock()
        self._node_id = MagicMock()

        self._event_system = MagicMock()
        self._data_factory = MagicMock()
        self._vote_factory = MagicMock()

        self._logger = MagicMock()
        self._messages = MagicMock()

        self._vote_timeout_started = MagicMock()

        self.round_start = AsyncMock()
        self.receive_vote = AsyncMock()
        self.receive_data = AsyncMock()
