from collections.abc import Mapping
from typing import Any, ClassVar, Literal, TypeAlias, TypeVar, overload
from ._access import AttributeAccess
from ._categories import Category as Category, ContentModel as ContentModel
from ._compose import Composable
from ._construct import Construction
from ._display import Displayable
from ._query import Queryable
from ._tree import TreeEditing
from .structure import Use

__all__ = ["AttrValue", "Category", "Child", "ContentModel", "Element"]

E = TypeVar('E', bound='Element')
T = TypeVar('T')
C = TypeVar('C', 'Element', str)
AttrValue: TypeAlias = Any
Child: TypeAlias = Element | str

class Element(Construction, AttributeAccess, TreeEditing, Queryable, Displayable, Composable):
    tag: ClassVar[str]
    namespace: ClassVar[str | None]
    category: ClassVar[Category]
    content: ClassVar[ContentModel]
    attributes: dict[str, AttrValue]
    children: list[Child]
    parent: Element | None
    id: str | None

    def __init_subclass__(
        cls,
        *,
        tag: str | None = None,
        category: Category | None = None,
        content: ContentModel | None = None,
        **kwargs: Any,
    ) -> None: ...
    def __init__(
        self,
        *children: Child,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **extra: AttrValue,
    ) -> None: ...
    def __getattr__(self, name: str) -> AttrValue: ...
    def __setattr__(self, name: str, value: AttrValue) -> None: ...
    def __delattr__(self, name: str) -> None: ...
    @property
    def animate(self) -> Any: ...
    def computed(self, name: str, default: object = None) -> object: ...
    @overload
    def clone(self: E, linked: Literal[False] = False) -> E: ...
    @overload
    def clone(self, linked: Literal[True]) -> Use: ...
    def copy(self, linked: bool = False) -> Element: ...
    def __copy__(self: E) -> E: ...
    def __deepcopy__(self: E, memo: dict[int, object]) -> E: ...
