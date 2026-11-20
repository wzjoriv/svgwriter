"""
Document content access: ``+=``, iteration, ``len``, indexing by position or id, membership.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import overload

from .._internal._constants import NON_CONTENT
from .._internal._typing import Self
from ..elements.core._container import flatten
from ..elements.core._element import Element
from .ingest import SupportsSVG, _ingest

__all__ = ["Access"]


class Access:
    """Sequence-like access to the top-level content; mixed into :class:`~svgwriter.Document`."""

    def __iadd__(self, elements: Element | SupportsSVG | Iterable[Element]) -> Self:
        for element in flatten(_ingest(elements)):
            self._place(element)  # type: ignore[type-var]
        return self

    def _content(self) -> list[Element]:
        return [c for c in self.root if c.tag not in NON_CONTENT]

    def __iter__(self) -> Iterator[Element]:
        """Top-level content elements (``<defs>``, ``<style>``, ``<title>``, ``<desc>`` skipped).

        Use ``doc.root.iter()`` to walk the whole tree.
        """
        return iter(self._content())

    def __len__(self) -> int:
        return len(self._content())

    @overload
    def __getitem__(self, key: int) -> Element: ...
    @overload
    def __getitem__(self, key: slice) -> list[Element]: ...
    @overload
    def __getitem__(self, key: str) -> Element: ...
    def __getitem__(self, key: int | slice | str) -> Element | list[Element]:
        """``doc[0]`` (top-level content by position), ``doc[1:3]`` or ``doc["logo"]`` (any element by id).

        Parameters
        ----------
        key : int, slice or str
            A position or slice among the top-level content, or an element id.

        Returns
        -------
        Element or list of Element
            The element, or a list for a slice.

        Raises
        ------
        IndexError, KeyError
            When nothing is at that position or has that id.

        Examples
        --------
        >>> from svgwriter import Document
        >>> doc = Document(10, 10)
        >>> _ = doc.rect(0, 0, 5, 5, id="logo")
        >>> doc[0] is doc["logo"]
        True
        """
        if isinstance(key, str):
            element = self.root.get_element_by_id(key)
            if element is None:
                raise KeyError(f"no element with id {key!r}")
            return element
        return self._content()[key]

    def __setitem__(self, key: int | str, element: Element) -> None:
        """``doc[0] = el`` or ``doc["logo"] = el``: put *el* where that element is (an explicit id moves to *el*).

        Examples
        --------
        >>> import svgwriter as svg
        >>> doc = svg.Document(10, 10)
        >>> _ = doc.rect(0, 0, 5, 5, id="logo")
        >>> doc["logo"] = svg.circle(5, 5, 2)
        >>> doc[0].tag, doc[0].id
        ('circle', 'logo')
        """
        from ..elements._behavior._geometry import replace_in_parent

        replace_in_parent(self[key], _ingest(element))

    def __contains__(self, item: object) -> bool:
        if isinstance(item, str):
            return self.root.get_element_by_id(item) is not None
        return isinstance(item, Element) and any(e is item for e in self.root.iter())

    def get_element_by_id(self, element_id: str) -> Element | None:
        """Find an element anywhere in the tree by its id.

        Parameters
        ----------
        element_id : str
            The id to look for.

        Returns
        -------
        Element or None
            The element, or None when no element has that id.

        See Also
        --------
        __getitem__ : ``doc["id"]`` raises instead of returning None.

        Examples
        --------
        >>> from svgwriter import Document
        >>> doc = Document(10, 10)
        >>> _ = doc.rect(0, 0, 5, 5, id="logo")
        >>> doc.get_element_by_id("logo").tag, doc.get_element_by_id("none")
        ('rect', None)
        """
        return self.root.get_element_by_id(element_id)
