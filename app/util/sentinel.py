from enum import Enum


class Sentinel(Enum):
    missing = None


MISSING = Sentinel.missing
