"""
``Theme``: an immutable palette, fonts and role styles; the theme in effect; the registry of named themes.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from contextvars import ContextVar, Token
from types import MappingProxyType, TracebackType
from typing import Any, Final, TypeAlias

from ..._internal._registry import Registry
from ...errors import ThemeError
from ..attributes.style import Style, StyleLike, StyleSheet
from ._constants import DEFAULT_THEME, ROLE_ATTRIBUTES, ROLE_CLASS_PREFIX
from ._files import ThemeFiles
from ._resolve import check_role_name, resolve_role
from ._roles import DERIVED_PALETTE, STANDARD_ROLES
from .fonts import Fonts
from .palette import Palette, PaletteSource

__all__ = ["themes", "RoleSource", "Theme"]

RoleSource: TypeAlias = "StyleLike | Callable[[Theme], StyleLike]"

themes: Final[Registry[Theme]] = Registry("theme")
"""Every theme by name: ``svg.themes.register(theme)`` adds one, ``list()``, ``get(name)`` and ``unregister(name)``."""
_ACTIVE: ContextVar[Theme | None] = ContextVar("svgwriter_theme", default=None)
_TOKENS: ContextVar[tuple[Token[Theme | None], ...]] = ContextVar("svgwriter_theme_tokens", default=())


class Theme(ThemeFiles):
    """Colors, fonts and the styles of named roles, applied to documents as CSS classes.

    Parameters
    ----------
    name : str
        A short name, used by :meth:`get` once registered and written to theme files.
    palette : Palette or mapping
        Color roles (see :class:`Palette`). ``border``, ``muted`` and ``shadow`` are derived from
        ``foreground`` and ``background``, and ``on_primary`` from ``primary``, unless given.
    fonts : Fonts, optional
        Families, sizes and weights. Defaults to ``Fonts()``.
    roles : mapping of str to style or callable, optional
        Extra or replaced role styles, merged over the standard roles. Each is a mapping of CSS
        properties (values may be literals, ``"{palette.name}"``/``"{fonts.sizes.name}"``
        references, expressions such as ``"={fonts.sizes.text} * 1.5"`` or functions of the theme) or a
        function of the theme returning one.
        Defaults to None.

    Raises
    ------
    ThemeError
        If a role name is invalid or anything cannot be resolved.

    See Also
    --------
    svgwriter.Document : Takes ``theme=``; elements opt in with ``as_role``.

    Notes
    -----
    A theme never changes. :meth:`replace` builds variants, and ``with theme:`` makes it the default
    for documents created in the block (a context variable, so threads and tasks stay separate).
    Outside any block the default is the registered ``"light"`` theme.

    Examples
    --------
    >>> import svgwriter as svg
    >>> dark = svg.themes.get("dark")
    >>> dark.style("box")["fill"].hex
    '#1f2937'
    >>> brand = dark.replace(name="brand", palette={"primary": "#ff6600"})
    >>> brand.style("shape")["fill"].hex
    '#ff6600'
    >>> with brand:
    ...     svg.Document(10, 10).theme.name
    'brand'
    """

    __slots__ = ("_class_rules", "_document", "_extends", "_fonts", "_name", "_palette", "_roles", "_styles")

    def __init__(self, name: str, palette: Palette | Mapping[str, PaletteSource], fonts: Fonts | None = None,
                 roles: Mapping[str, RoleSource] | None = None) -> None:
        sources = palette.sources if isinstance(palette, Palette) else palette
        object.__setattr__(self, "_name", str(name))
        object.__setattr__(self, "_palette", Palette({**DERIVED_PALETTE, **sources}))
        object.__setattr__(self, "_fonts", fonts if fonts is not None else Fonts())
        merged = {check_role_name(k): v for k, v in {**STANDARD_ROLES, **(roles or {})}.items()}
        object.__setattr__(self, "_roles", MappingProxyType(merged))
        object.__setattr__(self, "_styles", {k: resolve_role(self, k, v) for k, v in merged.items()})
        object.__setattr__(self, "_extends", None)
        object.__setattr__(self, "_document", None)
        object.__setattr__(self, "_class_rules", None)

    def _from_file(self, extends: str | None, document: str | None) -> Theme:
        object.__setattr__(self, "_extends", extends)
        object.__setattr__(self, "_document", document)
        return self

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError("Theme is immutable; use replace()")

    @property
    def name(self) -> str:
        """The theme's name."""
        return self._name

    @property
    def palette(self) -> Palette:
        """The resolved color roles."""
        return self._palette

    @property
    def fonts(self) -> Fonts:
        """Font families, sizes and weights."""
        return self._fonts

    @property
    def extends(self) -> str | None:
        """The registered theme this one is a variant of, or None; files write it as ``extends``.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.themes.get("dark").replace(name="night").extends
        'dark'
        >>> svg.themes.get("dark").extends is None
        True
        """
        return self._extends

    @property
    def roles(self) -> Mapping[str, RoleSource]:
        """Every role's source, standard roles included, as given."""
        return self._roles

    def style(self, role: str) -> Style:
        """The resolved style of *role* (a copy).

        Parameters
        ----------
        role : str
            The role name, such as ``"box"`` or ``"arrow.head"``.

        Returns
        -------
        Style
            CSS declarations with colors resolved.

        Raises
        ------
        ThemeError
            If the theme has no such role.

        Examples
        --------
        >>> import svgwriter as svg
        >>> str(svg.themes.get("light").style("line"))
        'fill:none;stroke:#0f766e;stroke-width:2px'
        """
        if role not in self._styles:
            raise ThemeError(f"theme {self._name!r} has no role {role!r}")
        return Style(self._styles[role])

    @staticmethod
    def class_name(role: str) -> str:
        """The CSS class that marks elements of *role*: ``role-`` plus the name with dots as dashes.

        Parameters
        ----------
        role : str
            The role name.

        Returns
        -------
        str
            The class name.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.Theme.class_name("arrow.head")
        'role-arrow-head'
        """
        return ROLE_CLASS_PREFIX + check_role_name(role).replace(".", "-")

    def css(self, roles: Iterable[str] | None = None) -> StyleSheet:
        """A style sheet with one ``.role-<name>`` rule per role.

        Parameters
        ----------
        roles : iterable of str, optional
            The roles to include, in theme order. Defaults to None, which includes every role.

        Returns
        -------
        StyleSheet
            The rules.

        Raises
        ------
        ThemeError
            If a requested role is not in the theme.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.themes.get("mono").css(["dot"]).css()
        '.role-dot { fill:#000000;stroke:#000000;stroke-width:1px }'
        """
        wanted = set(self._styles) if roles is None else set(roles)
        missing = sorted(wanted - set(self._styles))
        if missing:
            raise ThemeError(f"theme {self._name!r} has no role {', '.join(map(repr, missing))}")
        return StyleSheet((f".{self.class_name(k)}", {p: x for p, x in v.items() if p not in ROLE_ATTRIBUTES})
                          for k, v in self._styles.items() if k in wanted)

    def attributes(self, role: str) -> dict[str, str]:
        """The geometry a role sets as attributes (``rx``, ``ry``, ``r``); SVG 1.1 CSS cannot style them.

        Parameters
        ----------
        role : str
            The role name.

        Returns
        -------
        dict of str to str
            Attribute names and values; empty when the role sets no geometry.

        Raises
        ------
        ThemeError
            If the theme has no such role.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.themes.get("light").replace(roles={"card": {"rx": "6"}}).attributes("card")
        {'rx': '6'}
        """
        return {name: value for name, value in self.style(role).items() if name in ROLE_ATTRIBUTES}

    def replace(self, *, name: str | None = None, palette: Mapping[str, PaletteSource] | None = None,
                fonts: Fonts | Mapping[str, Any] | None = None, roles: Mapping[str, RoleSource] | None = None) -> Theme:
        """A variant: palette entries, font values and role properties merge into this theme's.

        A variant of a registered theme extends it; a variant of anything else keeps what that
        theme extends and the file it was read from, so :meth:`save` writes only what changed.

        Parameters
        ----------
        name : str, optional
            The variant's name. Defaults to None, which keeps this name.
        palette : mapping, optional
            Palette sources to replace or add; derived roles follow. Defaults to None.
        fonts : Fonts or mapping, optional
            A whole :class:`Fonts`, or keywords of :meth:`Fonts.replace`. Defaults to None.
        roles : mapping, optional
            Role sources; a mapping merges property by property into the existing role, a
            function replaces it. Defaults to None.

        Returns
        -------
        Theme
            The new theme.

        Examples
        --------
        >>> import svgwriter as svg
        >>> light = svg.themes.get("light")
        >>> bold = light.replace(roles={"line": {"stroke-width": 4}}, fonts={"sizes": {"text": 16}})
        >>> str(bold.style("line")), bold.fonts.sizes["text"]
        ('fill:none;stroke:#0f766e;stroke-width:4px', 16)
        """
        merged = dict(self._roles)
        for role, source in (roles or {}).items():
            base = merged.get(role)
            if isinstance(source, Mapping) and isinstance(base, Mapping):
                merged[role] = {**Style(base), **Style(source)}
            else:
                merged[role] = source
        if isinstance(fonts, Mapping):
            fonts = self._fonts.replace(**fonts)
        variant = Theme(name if name is not None else self._name, self._palette.replace(**(palette or {})),
                        fonts if fonts is not None else self._fonts, merged)
        if themes.find(self._name, plugins=False) is self:
            return variant._from_file(self._name, None)
        return variant._from_file(self._extends, self._document)

    @staticmethod
    def current() -> Theme:
        """The theme in effect: the innermost ``with theme:`` block, else ``"light"``.

        Returns
        -------
        Theme
            The theme new documents use.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.Theme.current().name
        'light'
        >>> with svg.themes.get("dark"):
        ...     svg.Theme.current().name
        'dark'
        """
        active = _ACTIVE.get()
        return active if active is not None else themes.get(DEFAULT_THEME)

    @staticmethod
    def of(theme: Theme | str | None) -> Theme:
        """A theme from a theme, a registered name, or None for :meth:`current`.

        Parameters
        ----------
        theme : Theme or str or None
            What to resolve.

        Returns
        -------
        Theme
            The theme.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.Theme.of("dark") is svg.themes.get("dark"), svg.Theme.of(None).name
        (True, 'light')
        """
        if theme is None:
            return Theme.current()
        if isinstance(theme, str):
            return themes.get(theme)
        if not isinstance(theme, Theme):
            raise TypeError(f"expected a Theme or a theme name, got {type(theme).__name__}")
        return theme

    def __enter__(self) -> Theme:
        _TOKENS.set((*_TOKENS.get(), _ACTIVE.set(self)))
        return self

    def __exit__(self, kind: type[BaseException] | None, error: BaseException | None, trace: TracebackType | None) -> None:
        *rest, token = _TOKENS.get()
        _TOKENS.set(tuple(rest))
        _ACTIVE.reset(token)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Theme):
            return NotImplemented
        return (self._name, self._palette, self._fonts.to_dict(), self._style_texts()) == (
            other._name, other._palette, other._fonts.to_dict(), other._style_texts())

    def _style_texts(self) -> dict[str, dict[str, str]]:
        return {role: {k: str(v) for k, v in style.items()} for role, style in self._styles.items()}

    __hash__ = None  # type: ignore[assignment]

    def __repr__(self) -> str:
        return f"Theme({self._name!r})"
