"""
Document fonts: embedding the faces its text uses as ``@font-face`` rules.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .._internal._fonts import font_weight
from ..attributes.cascade import computed, rules_of
from ..elements.core import Category

if TYPE_CHECKING:
    from ..elements.structure import StyleElement
    from ..ops.typeface import Face, Typeface

__all__ = ["Typography"]


class Typography:
    """Font embedding; mixed into :class:`~svgwriter.Document`."""

    def used_faces(self, *typefaces: Typeface) -> list[Face]:
        """The faces the document's text uses, one per font file.

        Every text element's ``font-family`` list (style sheets and theme roles
        included) is matched against the typefaces, and CSS font matching
        picks the face for its ``font-weight`` and ``font-style``.

        Parameters
        ----------
        *typefaces : Typeface
            The families to look for. Defaults to every :class:`~svgwriter.Typeface`
            made in this session.

        Returns
        -------
        list of Face
            The faces in first-use order; variable faces keep their whole range.

        See Also
        --------
        embed_fonts : Write these faces into the document.

        Examples
        --------
        >>> import svgwriter as svg
        >>> serif = svg.Typeface("serif")
        >>> doc = svg.Document(100, 40)
        >>> _ = doc.text("Hi", x=0, y=20, font_family=serif)
        >>> len(doc.used_faces(serif))
        1
        """
        from ..ops.typeface import known_typefaces

        known = {typeface.name.lower(): typeface for typeface in typefaces or known_typefaces()}
        faces: dict[int, Face] = {}
        with self._prepared():  # type: ignore[attr-defined]
            rules = rules_of(self.root)  # type: ignore[attr-defined]
            for element in self.root.iter():  # type: ignore[attr-defined]
                if element.category is not Category.TEXT_CONTENT:
                    continue
                families = str(computed(element, "font-family", "", rules)).split(",")
                weight = font_weight(computed(element, "font-weight", "normal", rules))
                style = str(computed(element, "font-style", "normal", rules)).strip() or "normal"
                for family in (name.strip().strip("'\"").lower() for name in families):
                    if family in known:
                        chosen = known[family].face(weight, style)  # type: ignore[arg-type]
                        original = next(face for face in known[family].faces if face.typeface is chosen.typeface)
                        faces.setdefault(id(original), original)
                        break
        return list(faces.values())

    def embed_fonts(self, *typefaces: Typeface) -> StyleElement | None:
        """Add ``@font-face`` rules carrying the used fonts, so the SVG file shows them anywhere.

        Only the faces the text actually uses are written, each once, as base64
        data URIs in a ``<style>`` at the top of the document. Call it once,
        after the text is in place.

        Parameters
        ----------
        *typefaces : Typeface
            The families to embed. Defaults to every :class:`~svgwriter.Typeface`
            made in this session.

        Returns
        -------
        StyleElement or None
            The new ``<style>``, or None when no text uses the typefaces.

        See Also
        --------
        used_faces : The faces that would be written.
        Typeface.css : The rules of one family.

        Examples
        --------
        >>> import svgwriter as svg
        >>> sans = svg.Typeface("sans-serif")
        >>> doc = svg.Document(100, 40)
        >>> _ = doc.text("Hi", x=0, y=20, font=sans)
        >>> "@font-face" in doc.embed_fonts(sans).css
        True
        """
        faces = self.used_faces(*typefaces)
        if not faces:
            return None
        return self.style("\n".join(face.css() for face in faces))  # type: ignore[attr-defined]
