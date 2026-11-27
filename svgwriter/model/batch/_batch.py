"""
The ``Batch`` group: many similar items held as numpy columns until they are needed one by one.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, overload

import numpy as np

from ..._internal._typing import Self
from ..attributes.cascade import INHERITED
from ..attributes.names import svg_name
from ..elements.core import Element
from ..elements.structure import Defs, Group
from ._columns import Columns, broadcast
from ._expand import build_items, item_markup_names
from ._kinds import INSTANCES, Kind
from ._markup import item_markup
from ._measure import ItemMeasures
from ._transforms import ItemTransforms

if TYPE_CHECKING:
    from ._motion import BatchMotion

__all__ = ["Batch"]


class Batch(ItemTransforms, ItemMeasures, Group):
    """A ``<g>`` of many similar items (circles, rects, lines, polylines, texts or instances).

    Made by :func:`~svgwriter.model.batch.circles` and the other factories of
    :mod:`svgwriter.batch <svgwriter.model.batch>`. While *compact* the items live as numpy
    columns: building, transforming (:meth:`translate`, :meth:`rotate`, :meth:`scale`), restyling
    (:meth:`set`) and writing them are vectorized, and the output is one ordinary SVG element per
    item. Reading an item (``batch[i]``, iteration, :attr:`items`) or animating items
    (:attr:`animate`) *expands* the batch: the items become real child elements, edited like any
    other, and the batch methods keep working on them one by one.

    Values given once for every item go on the ``<g>`` when they are inherited (``fill``,
    ``stroke``, ``font-size``...) and on each item otherwise (``opacity``). Style the whole batch
    through the ``<g>``: ``batch.as_role("dot")``, ``batch.matrix``, ``batch.id``.

    See Also
    --------
    svgwriter.model.batch.circles : Make a batch of circles.

    Notes
    -----
    Exporters that draw shape by shape (PDF, PowerPoint, TikZ, ...) expand a copy; the raster
    renderer draws compact batches directly. Style sheet rules that select items individually
    (``circle { ... }``) style expanded items only.

    Examples
    --------
    >>> import numpy as np
    >>> import svgwriter as svg
    >>> dots = svg.batch.circles(np.arange(3) * 10, 5, 2, fill="teal")
    >>> print(dots.to_string(pretty=False, xml_declaration=False))
    <g fill="teal"><circle cx="0" cy="5" r="2"/><circle cx="10" cy="5" r="2"/><circle cx="20" cy="5" r="2"/></g>
    >>> len(dots), dots.compact
    (3, True)
    >>> dots[1].r = 4
    >>> dots.compact, dots[1].r
    (False, 4.0)
    """

    _kind: Kind
    _count: int
    _columns: dict[str, np.ndarray] | None
    _matrix: np.ndarray | None
    _points: np.ndarray | None
    _offsets: np.ndarray | None
    _content: np.ndarray | None

    @classmethod
    def _create(cls, kind: Kind, columns: Columns, *, points: np.ndarray | None = None,
                offsets: np.ndarray | None = None, content: np.ndarray | None = None,
                shape: Element | None = None) -> Batch:
        batch = cls()
        batch.__dict__.update(_kind=kind, _count=columns.count, _columns=columns.items, _matrix=None,
                              _points=points, _offsets=offsets, _content=content)
        for name, value in columns.shared.items():
            batch.set(name, value)
        if shape is not None:
            batch.append(Defs(shape))
        return batch

    @property
    def compact(self) -> bool:
        """Whether the items are still columns (True) or real child elements (False).

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.batch.circles([1, 2], 0, 1).compact
        True
        """
        return self._columns is not None

    @property
    def item_type(self) -> type[Element]:
        """The element class of every item (``svg.Circle`` for circles and dots, ``svg.Use`` for instances).

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.batch.points([1, 2], 0).item_type.__name__
        'Circle'
        """
        return self._kind.element

    @property
    def shape(self) -> Element | None:
        """The element an instance batch repeats (in the batch's ``<defs>``); None for other batches.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.batch.instances(svg.rect(0, 0, 4, 4), [0, 10], 0).shape.tag
        'rect'
        """
        if self._kind is not INSTANCES or not self.children or not isinstance(self.children[0], Defs):
            return None
        return next(iter(self.children[0]), None)

    @property
    def items(self) -> list[Element]:
        """The items as elements, expanding the batch first.

        Returns
        -------
        list of Element
            One child per item, in drawing order.

        Examples
        --------
        >>> import svgwriter as svg
        >>> [item.tag for item in svg.batch.lines(0, 0, [5, 10], 5).items]
        ['line', 'line']
        """
        self.expand()
        return [child for child in self.children if isinstance(child, Element) and not isinstance(child, Defs)]

    def expand(self) -> Self:
        """Turn the columns into one real child element per item and return the batch.

        Expanding is one-way and happens by itself on ``batch[i]``, iteration, :attr:`items` and
        :attr:`animate`; afterwards every method works item by item.

        Returns
        -------
        Batch
            This batch.

        Examples
        --------
        >>> import svgwriter as svg
        >>> dots = svg.batch.circles([1, 2], 0, 1).expand()
        >>> dots.compact, [child.tag for child in dots.children]
        (False, ['circle', 'circle'])
        """
        if self._columns is not None:
            items = build_items(self)
            self.children.extend(items)
            self.__dict__.update(_columns=None, _matrix=None, _points=None, _offsets=None, _content=None)
        return self

    def __len__(self) -> int:
        return self._count if self._columns is not None else len(self.items)

    def __iter__(self) -> Iterator[Element]:
        return iter(self.items)

    @overload
    def __getitem__(self, index: int) -> Element: ...
    @overload
    def __getitem__(self, index: slice) -> list[Element]: ...
    def __getitem__(self, index: int | slice) -> Element | list[Element]:
        if not isinstance(index, (int, slice)):
            raise TypeError(f"batch items are indexed by position or slice, not {type(index).__name__}")
        return self.items[index]

    @property
    def animate(self) -> BatchMotion:
        """Animation presets applied to every item, optionally staggered: ``batch.animate.fade_in(1, stagger=0.01)``.

        Expands the batch. Array arguments with one value per item go to their own item.

        Returns
        -------
        BatchMotion
            Every :attr:`Element.animate <svgwriter.model.elements.Element.animate>` preset.

        Examples
        --------
        >>> import svgwriter as svg
        >>> dots = svg.batch.circles([0, 10, 20], 0, 2)
        >>> _ = dots.animate.fade_in(0.5, stagger=0.1)
        >>> [item.children[0].get("begin") for item in dots]
        ['0s', '0.1s', '0.2s']
        """
        from ._motion import BatchMotion

        return BatchMotion(self)

    def column(self, name: str) -> np.ndarray:
        """Every item's value of attribute *name* (Python or SVG spelling), or ``"transform"`` as ``(N, 6)``.

        Parameters
        ----------
        name : str
            The attribute.

        Returns
        -------
        numpy.ndarray
            One value per item (read-only while compact); items without the attribute give None.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.batch.circles([1, 2], 0, [3, 4]).column("r").tolist()
        [3.0, 4.0]
        """
        key = svg_name(name)
        if self._columns is None:
            if key == "transform":
                matrices = [item.matrix for item in self.items]  # type: ignore[attr-defined]
                return np.array([[m.a, m.b, m.c, m.d, m.e, m.f] for m in matrices])
            return np.array([item.get(key) for item in self.items])
        if key == "transform":
            return self._matrices()
        if key not in self._columns:
            return np.full(self._count, None, dtype=object)
        return self._columns[key]

    def set(self, name: str | None = None, value: Any = None, **attributes: Any) -> Self:  # type: ignore[override]
        """Set attributes on every item; arrays give each item its own value. Returns the batch.

        Parameters
        ----------
        name, value : str and object, optional
            One attribute by name, as :meth:`Element.set <svgwriter.model.elements.Element.set>` takes it.
        **attributes
            Attributes in Python spelling: scalars apply to every item (inherited ones go on the
            ``<g>``), arrays and colour lists broadcast over the items, ``None`` removes.

        Returns
        -------
        Batch
            This batch.

        Raises
        ------
        ValueError
            If an array does not broadcast to one value per item.

        Examples
        --------
        >>> import svgwriter as svg
        >>> dots = svg.batch.circles([0, 10], 0, 2).set(fill=["red", "blue"], r=[1, 5])
        >>> dots.column("fill").tolist(), dots.column("r").tolist()
        (['#ff0000', '#0000ff'], [1.0, 5.0])
        """
        if name is not None:
            attributes[name] = value
        if "_kind" not in self.__dict__:
            for key, given in attributes.items():
                super().set(key, given)
            return self
        removed = [svg_name(key) for key, given in attributes.items() if given is None]
        columns = broadcast({}, attributes, count=len(self))
        if self._columns is None:
            self._set_items(removed, columns)
            return self
        for key in removed:
            self._columns.pop(key, None)
            super().set(key, None)
        for key, column in columns.items.items():
            super().set(key, None)
            self._columns[key] = column
        for key, given in columns.shared.items():
            self._columns.pop(key, None)
            super().set(key, given)
        return self

    def _set_items(self, removed: list[str], columns: Columns) -> None:
        items = self.items
        for key in removed:
            super().set(key, None)
            for item in items:
                item.set(key, None)
        for key, column in columns.items.items():
            for item, value in zip(items, column.tolist(), strict=True):
                item.set(key, value)
        for key, given in columns.shared.items():
            super().set(key, given)
            if key in INHERITED:
                for item in items:
                    item.set(key, None)

    def _blend(self, other: Batch, t: float) -> Batch:
        """The batch a fraction *t* of the way to *other*; :func:`svgwriter.interpolate` calls it."""
        from ._blend import blend

        return blend(self, other, t)

    def item_markup(self, precision: int = 4) -> list[str]:
        """Each item of a compact batch as SVG text, as the writer puts it inside the ``<g>``.

        Parameters
        ----------
        precision : int, optional
            Maximum decimals for numbers. Defaults to 4.

        Returns
        -------
        list of str
            One element per item; empty once the batch has expanded.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.batch.rects([0, 5], 0, 4, 2.5).item_markup()
        ['<rect x="0" y="0" width="4" height="2.5"/>', '<rect x="5" y="0" width="4" height="2.5"/>']
        """
        return item_markup(self, precision) if self._columns is not None else []

    @property
    def item_attributes(self) -> list[str]:
        """SVG names of the attributes a compact batch writes on every item (empty once expanded).

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.batch.circles([1, 2], 0, 1, opacity=[0.5, 1]).item_attributes
        ['cx', 'cy', 'r', 'opacity']
        """
        return item_markup_names(self) if self._columns is not None else []

    def clone(self, linked: bool = False) -> Any:  # type: ignore[override]
        """A deep copy that shares the read-only columns; see :meth:`Element.clone <svgwriter.model.elements.Element.clone>`.

        Examples
        --------
        >>> import svgwriter as svg
        >>> dots = svg.batch.circles([1, 2], 0, 1)
        >>> copy = dots.clone().translate(5)
        >>> dots.column("transform")[0, 4].item(), copy.column("transform")[0, 4].item()
        (0.0, 5.0)
        """
        duplicate = super().clone(linked)
        if not linked and self._columns is not None:
            duplicate.__dict__["_columns"] = dict(self._columns)
        return duplicate
