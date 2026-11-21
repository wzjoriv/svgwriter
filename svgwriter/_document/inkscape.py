"""
Inkscape layers, guides and export hints on a document.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..inkscape import (
    ExportHints,
    Guide,
    export_hints,
    guides,
    is_layer,
    layers,
    new_layer,
    set_export_hints,
    set_guides,
)

if TYPE_CHECKING:
    from ..model.elements.structure import Group

__all__ = ["InkscapeData"]


class InkscapeData:
    """Layers, guides and export hints; mixed into :class:`~svgwriter.Document`."""

    def layer(self, label: str, **kwargs: Any) -> Group:
        """The Inkscape layer called *label* at the insertion point, added if missing.

        Use it with ``with`` to draw into the layer; inside another layer it
        finds or adds a sublayer.

        Parameters
        ----------
        label : str
            The name shown in Inkscape's Layers panel.
        **kwargs
            Attributes for a new layer's ``<g>``.

        Returns
        -------
        Group
            The existing or new layer.

        See Also
        --------
        layers : Every layer by label.

        Examples
        --------
        >>> import svgwriter as svg
        >>> doc = svg.Document(100, 100)
        >>> with doc.layer("Background"):
        ...     _ = doc.rect(0, 0, 100, 100, fill="navy")
        >>> doc.layer("Background") is doc.layers["Background"], len(doc.layers["Background"])
        (True, 1)
        """
        for child in self.current:  # type: ignore[attr-defined]
            if is_layer(child) and child.label == label:
                return child  # type: ignore[no-any-return]
        return self._place(new_layer(label, **kwargs))  # type: ignore[attr-defined, no-any-return]

    @property
    def layers(self) -> dict[str, Group]:
        """Every layer and sublayer by label, in document order.

        Examples
        --------
        >>> import svgwriter as svg
        >>> doc = svg.Document.from_string(
        ...     '<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape">'
        ...     '<g inkscape:groupmode="layer" inkscape:label="Ink"/></svg>')
        >>> list(doc.layers)
        ['Ink']
        """
        return layers(self.root)  # type: ignore[attr-defined]

    @property
    def guides(self) -> list[Guide]:
        """Inkscape's guide lines, in user units; assign a list to replace them.

        Examples
        --------
        >>> import svgwriter as svg
        >>> doc = svg.Document(100, 50)
        >>> doc.guides = [svg.inkscape.Guide.vertical(25), svg.inkscape.Guide.horizontal(10, label="base")]
        >>> [(g.x, g.y, g.angle) for g in doc.guides]
        [(25.0, 0.0, 90.0), (0.0, 10.0, 0.0)]
        """
        return guides(self.root)  # type: ignore[attr-defined]

    @guides.setter
    def guides(self, value: list[Guide]) -> None:
        set_guides(self.root, list(value))  # type: ignore[attr-defined]

    def guide(self, x: float | None = None, y: float | None = None, *, angle: float | None = None,
              **kwargs: Any) -> Guide:
        """Add an Inkscape guide line and return it.

        Parameters
        ----------
        x, y : float, optional
            Give `x` alone for a vertical guide, `y` alone for a horizontal one,
            or both with `angle` for a slanted guide through that point.
        angle : float, optional
            Direction in degrees, clockwise from the x axis. Defaults to None,
            which follows from the coordinates given.
        **kwargs
            ``label``, ``color`` or ``locked`` (see :class:`~svgwriter.inkscape.Guide`).

        Returns
        -------
        Guide
            The new guide.

        Raises
        ------
        TypeError
            If neither `x` nor `y` is given.

        Examples
        --------
        >>> import svgwriter as svg
        >>> doc = svg.Document(100, 100)
        >>> doc.guide(x=50).angle, doc.guide(50, 50, angle=45).angle, len(doc.guides)
        (90.0, 45, 2)
        """
        if x is None and y is None:
            raise TypeError("give x for a vertical guide, y for a horizontal one, or both with angle=")
        if y is None:
            line = Guide.vertical(x, **kwargs) if angle is None else Guide(x, 0.0, angle, **kwargs)  # type: ignore[arg-type]
        elif x is None:
            line = Guide.horizontal(y, **kwargs) if angle is None else Guide(0.0, y, angle, **kwargs)
        else:
            line = Guide(x, y, 0.0 if angle is None else angle, **kwargs)
        self.guides = [*self.guides, line]
        return line

    @property
    def export_hints(self) -> ExportHints:
        """Inkscape's export resolution, file name and document units; assign to change them.

        Raster exports (``doc.save("a.png")``) use the stored resolution when no
        ``scale``, ``dpi`` or ``size`` is given.

        Examples
        --------
        >>> import svgwriter as svg
        >>> doc = svg.Document(10, 10)
        >>> doc.export_hints = svg.inkscape.ExportHints(dpi=192)
        >>> png = doc.export("png")
        >>> doc.export_hints.dpi, int.from_bytes(png[16:20], "big")
        (192.0, 20)
        """
        return export_hints(self.root)  # type: ignore[attr-defined]

    @export_hints.setter
    def export_hints(self, value: ExportHints) -> None:
        set_export_hints(self.root, value)  # type: ignore[attr-defined]
