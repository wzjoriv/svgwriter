"""
Named canvas sizes: paper, slides, video, social images and icons (``Document(size="a4")``).
"""

from __future__ import annotations

from dataclasses import dataclass

from .._internal._presets import SIZES
from ..errors import UnknownNameError
from ..model.units.lengths import Length, LengthLike, Unit
from ._constants import BUILTIN_SIZES, IDENTIFIER_SEPARATORS, LANDSCAPE_SUFFIX, PORTRAIT_SUFFIX

__all__ = ["PageSize", "page_size", "size"]


def _length(value: LengthLike) -> Length:
    return value if isinstance(value, Length) else Length.parse(value) if isinstance(value, str) else Length(float(value))


def _identifier(name: str) -> str:
    return IDENTIFIER_SEPARATORS.sub("_", name).strip("_")


@dataclass(frozen=True, slots=True)
class PageSize:
    """A canvas size: a width and a height counted in one unit.

    Look the built-in ones up as attributes of :data:`svgwriter.size` (``svg.size.a4``), add your own
    with :data:`svgwriter.catalog.preset.size`, and pass either to ``Document(size=...)``, ``Scene.size`` or a
    project's ``size``.

    Parameters
    ----------
    width, height : float
        The two sides, in `units`.
    units : Unit, optional
        The unit both sides are counted in. Defaults to ``Unit.NONE``, user units (pixels).

    See Also
    --------
    svgwriter.size : The built-in sizes by name.
    svgwriter.catalog.preset.size : Register a size under a name.

    Examples
    --------
    >>> import svgwriter as svg
    >>> a4 = svg.size.a4
    >>> a4
    PageSize(width=210.0, height=297.0, units=<Unit.MM: 'mm'>)
    >>> str(a4.landscape), a4.landscape.portrait == a4
    ('297mm x 210mm', True)
    >>> svg.Document(size=a4.landscape).root.get("viewBox").width
    297.0
    """

    width: float
    height: float
    units: Unit = Unit.NONE

    @classmethod
    def of(cls, width: LengthLike, height: LengthLike) -> PageSize:
        """A size from two lengths of one unit.

        Parameters
        ----------
        width, height : Length, float or str
            A :class:`~svgwriter.Length`, length text such as ``"50cm"``, or pixels.

        Returns
        -------
        PageSize
            The size.

        Raises
        ------
        ValueError
            If the two lengths have different units.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.PageSize.of("50cm", "70cm")
        PageSize(width=50.0, height=70.0, units=<Unit.CM: 'cm'>)
        """
        first, second = _length(width), _length(height)
        if first.unit is not second.unit:
            raise ValueError(f"width and height need one unit, not {first} and {second}")
        return cls(first.value, second.value, first.unit)

    @property
    def lengths(self) -> tuple[Length, Length]:
        """``(width, height)`` as :class:`~svgwriter.Length` values."""
        return Length(self.width, self.units), Length(self.height, self.units)

    @property
    def landscape(self) -> PageSize:
        """The same size with the long side across."""
        return self if self.width >= self.height else PageSize(self.height, self.width, self.units)

    @property
    def portrait(self) -> PageSize:
        """The same size with the long side down."""
        return self if self.height >= self.width else PageSize(self.height, self.width, self.units)

    def __str__(self) -> str:
        width, height = self.lengths
        return f"{width} x {height}"


class _Sizes:
    """The registered sizes as attributes: ``svg.size.a4``, ``svg.size.slide_16_9``, ``svg.size.<your own>``."""

    a0: PageSize
    a1: PageSize
    a2: PageSize
    a3: PageSize
    a4: PageSize
    a5: PageSize
    a6: PageSize
    letter: PageSize
    legal: PageSize
    tabloid: PageSize
    business_card: PageSize
    slide_16_9: PageSize
    slide_4_3: PageSize
    video_720p: PageSize
    video_1080p: PageSize
    instagram_post: PageSize
    instagram_portrait: PageSize
    instagram_story: PageSize
    og_image: PageSize
    youtube_thumbnail: PageSize
    favicon: PageSize
    apple_touch_icon: PageSize
    icon: PageSize

    def __getattr__(self, name: str) -> PageSize:
        for registered in SIZES:
            if _identifier(registered) == name:
                return SIZES.get(registered)
        raise AttributeError(f"no size {name!r}; svg.preset.size.list() lists every size")

    def __dir__(self) -> list[str]:
        return [_identifier(registered) for registered in SIZES]

    def __repr__(self) -> str:
        return f"size({', '.join(dir(self))})"


size = _Sizes()
"""The registered sizes as attributes, names turned into identifiers (``"slide-16:9"`` is ``size.slide_16_9``).

Every attribute is a :class:`PageSize`; sizes added with :data:`svgwriter.catalog.preset.size` appear here too.
"""


def page_size(size: str | PageSize) -> tuple[Length, Length]:
    """The width and height of a size, turned for a ``-landscape`` or ``-portrait`` suffix.

    Parameters
    ----------
    size : str or PageSize
        A :class:`PageSize`, or a name from ``svg.preset.size.list()`` (``"a4"``, ``"letter"``,
        ``"slide-16:9"``, ``"instagram-story"``, ...), optionally followed by ``-landscape`` (long side
        across) or ``-portrait`` (long side down).

    Returns
    -------
    tuple of Length
        ``(width, height)``.

    Raises
    ------
    UnknownNameError
        If the name is unknown; the message suggests the closest names.

    See Also
    --------
    svgwriter.catalog.preset.size : Add a size.

    Examples
    --------
    >>> import svgwriter as svg
    >>> [str(side) for side in svg.page_size("a4-landscape")]
    ['297mm', '210mm']
    >>> svg.page_size("a44")
    Traceback (most recent call last):
    ...
    svgwriter.errors.UnknownNameError: unknown size 'a44'; did you mean 'a4'? (svg.preset.size.list() lists every size)
    """
    if isinstance(size, PageSize):
        return size.lengths
    base, turn = size, None
    for suffix in (LANDSCAPE_SUFFIX, PORTRAIT_SUFFIX):
        if size.endswith(suffix) and SIZES.find(size, plugins=False) is None:
            base, turn = size.removesuffix(suffix), suffix
    page = SIZES.find(base)
    if page is None:
        raise UnknownNameError(f"{SIZES.unknown(size if turn is None else base)} (svg.preset.size.list() lists every size)")
    if turn is not None:
        page = page.landscape if turn == LANDSCAPE_SUFFIX else page.portrait
    return page.lengths


for _name, (_width, _height) in BUILTIN_SIZES.items():
    SIZES.add_builtin(_name, PageSize.of(_width, _height))
