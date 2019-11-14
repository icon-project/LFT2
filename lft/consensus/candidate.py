from dataclasses import dataclass
from typing import Sequence

from lft.consensus.messages.data import Data
from lft.consensus.messages.vote import Vote


@dataclass(frozen=True)
class Candidate:
    data: Data
    votes: Sequence[Vote]
