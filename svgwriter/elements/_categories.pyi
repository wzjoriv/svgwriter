from enum import Enum, Flag

__all__ = ["Category", "ContentModel"]

class ContentModel(Flag):
    EMPTY = 0
    TEXT = 1
    ELEMENTS = 2
    MIXED = 3

class Category(Enum):
    ANIMATION = 1
    CONTAINER = 2
    DESCRIPTIVE = 3
    FILTER_PRIMITIVE = 4
    FONT = 5
    GRADIENT = 6
    GRAPHICS = 7
    LIGHT_SOURCE = 8
    SHAPE = 9
    STRUCTURAL = 10
    TEXT_CONTENT = 11
    PAINT_SERVER = 12
    OTHER = 13
    GROUPING = CONTAINER
