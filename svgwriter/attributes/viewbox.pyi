from dataclasses import dataclass
from enum import Enum
from typing import NamedTuple

__all__ = ["Align", "MeetOrSlice", "PreserveAspectRatio", "ViewBox"]

class ViewBox(NamedTuple):
    min_x: float
    min_y: float
    width: float
    height: float

    @classmethod
    def parse(cls, text: str) -> ViewBox: ...
    @property
    def aspect_ratio(self) -> float: ...
    def svg_value(self, precision: int = 4) -> str: ...

class Align(str, Enum):
    NONE = 'none'
    X_MIN_Y_MIN = 'xMinYMin'
    X_MID_Y_MIN = 'xMidYMin'
    X_MAX_Y_MIN = 'xMaxYMin'
    X_MIN_Y_MID = 'xMinYMid'
    X_MID_Y_MID = 'xMidYMid'
    X_MAX_Y_MID = 'xMaxYMid'
    X_MIN_Y_MAX = 'xMinYMax'
    X_MID_Y_MAX = 'xMidYMax'
    X_MAX_Y_MAX = 'xMaxYMax'
    CENTER = X_MID_Y_MID

class MeetOrSlice(str, Enum):
    MEET = 'meet'
    SLICE = 'slice'

@dataclass(frozen=True)
class PreserveAspectRatio:
    align: Align = Align.X_MID_Y_MID
    meet_or_slice: MeetOrSlice = MeetOrSlice.MEET
    defer: bool = False

    def __init__(
        self,
        align: Align = Align.X_MID_Y_MID,
        meet_or_slice: MeetOrSlice = MeetOrSlice.MEET,
        defer: bool = False,
    ) -> None: ...
    @classmethod
    def parse(cls, text: str) -> PreserveAspectRatio: ...
    def svg_value(self, precision: int = 4) -> str: ...
    def __str__(self) -> str: ...
