"""
Lighting primitives and light sources.
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from typing import Any

from ...color.color import Color
from .._mixins import CoreAttributes
from ..base import Category, Child, ContentModel
from .base import SingleInput

__all__ = [
    "FeDiffuseLighting",
    "FeDistantLight",
    "FePointLight",
    "FeSpecularLighting",
    "FeSpotLight",
    "LightSource",
    "Vector3",
]

Vector3 = tuple[float, float, float]


def _normalize(x: float, y: float, z: float) -> Vector3:
    length = math.sqrt(x * x + y * y + z * z) or 1.0
    return (x / length, y / length, z / length)


def _num(element: CoreAttributes, name: str, default: float = 0.0) -> float:
    return float(element.get(name, default))


class LightSource(CoreAttributes, ABC, category=Category.LIGHT_SOURCE, content=ContentModel.ELEMENTS):
    """Abstract light source; the child of a lighting primitive.

    Parameters
    ----------
    **kwargs
        Core and other SVG attributes in Python spelling.

    See Also
    --------
    FeDistantLight : Light from infinitely far away.
    FePointLight : A point light.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.FeDistantLight(0, 0).directional
    True
    """

    @property
    @abstractmethod
    def directional(self) -> bool:
        """``True`` when the light direction is the same everywhere.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.FePointLight().directional
        False
        """

    @abstractmethod
    def light_vector(self, x: float, y: float, z: float) -> Vector3:
        """Compute the direction from a surface point towards the light.

        Parameters
        ----------
        x, y, z : float
            The surface point.

        Returns
        -------
        tuple of float
            Unit vector ``(x, y, z)`` pointing at the light.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.FePointLight(0, 0, 10).light_vector(0, 0, 0)
        (0.0, 0.0, 1.0)
        """


class FeDistantLight(LightSource, tag="feDistantLight"):
    """``<feDistantLight>``: light from infinitely far away.

    Parameters
    ----------
    azimuth : float, optional
        Direction angle in the xy plane, in degrees. Defaults to 0.
    elevation : float, optional
        Angle above the xy plane, in degrees. Defaults to 0.
    **kwargs
        Core and other SVG attributes in Python spelling.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(svg.FeDistantLight(45, 60))
    '<feDistantLight azimuth="45" elevation="60"/>'
    """

    def __init__(self, azimuth: float = 0, elevation: float = 0, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.update(azimuth=azimuth, elevation=elevation)

    @property
    def directional(self) -> bool:
        """Always ``True``: the direction is the same everywhere.

        Returns
        -------
        bool
            ``True``.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.FeDistantLight(45, 60).directional
        True
        """
        return True

    def light_vector(self, x: float, y: float, z: float) -> Vector3:
        """The constant unit vector towards the light, independent of the point.

        Parameters
        ----------
        x, y, z : float
            The surface point; ignored, since the light is infinitely far away.

        Returns
        -------
        tuple of float
            Unit vector ``(x, y, z)`` pointing at the light.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.FeDistantLight(0, 0).light_vector(5, 5, 0)
        (1.0, 0.0, 0.0)
        """
        azimuth = math.radians(_num(self, "azimuth"))
        elevation = math.radians(_num(self, "elevation"))
        return (
            math.cos(azimuth) * math.cos(elevation),
            math.sin(azimuth) * math.cos(elevation),
            math.sin(elevation),
        )


class FePointLight(LightSource, tag="fePointLight"):
    """``<fePointLight>``: an omnidirectional point light.

    Parameters
    ----------
    x, y, z : float, optional
        Light position. Defaults to 0.
    **kwargs
        Core and other SVG attributes in Python spelling.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(svg.FePointLight(1, 2, 3))
    '<fePointLight x="1" y="2" z="3"/>'
    """

    def __init__(self, x: float = 0, y: float = 0, z: float = 0, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.update(x=x, y=y, z=z)

    @property
    def directional(self) -> bool:
        """Always ``False``: the direction depends on the surface point.

        Returns
        -------
        bool
            ``False``.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.FePointLight(1, 2, 3).directional
        False
        """
        return False

    def light_vector(self, x: float, y: float, z: float) -> Vector3:
        """The unit vector from the point towards the light position.

        Parameters
        ----------
        x, y, z : float
            The surface point.

        Returns
        -------
        tuple of float
            Unit vector ``(x, y, z)`` pointing at the light.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.FePointLight(0, 10, 0).light_vector(0, 0, 0)
        (0.0, 1.0, 0.0)
        """
        return _normalize(_num(self, "x") - x, _num(self, "y") - y, _num(self, "z") - z)


class FeSpotLight(FePointLight, tag="feSpotLight"):
    """``<feSpotLight>``: a point light aimed at ``pointsAt``.

    Parameters
    ----------
    x, y, z : float, optional
        Light position. Defaults to 0.
    points_at_x, points_at_y, points_at_z : float, optional
        The point the light aims at. Default to 0.
    specular_exponent : float, optional
        Focus of the light beam. Defaults to None.
    limiting_cone_angle : float, optional
        Half-angle of the cone in degrees. Defaults to None.
    **kwargs
        Core and other SVG attributes in Python spelling.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(svg.FeSpotLight(1, 2, 3, points_at_x=4))
    '<feSpotLight x="1" y="2" z="3" pointsAtX="4" pointsAtY="0" pointsAtZ="0"/>'
    """

    def __init__(
        self,
        x: float = 0,
        y: float = 0,
        z: float = 0,
        *,
        points_at_x: float = 0,
        points_at_y: float = 0,
        points_at_z: float = 0,
        specular_exponent: float | None = None,
        limiting_cone_angle: float | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(x, y, z, **kwargs)
        self.update(
            points_at_x=points_at_x,
            points_at_y=points_at_y,
            points_at_z=points_at_z,
            specular_exponent=specular_exponent,
            limiting_cone_angle=limiting_cone_angle,
        )


class _Lighting(SingleInput):
    def __init__(
        self,
        *light: Child,
        surface_scale: float | None = None,
        kernel_unit_length: float | tuple[float, float] | None = None,
        lighting_color: Color | str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*light, **kwargs)
        self.update(surface_scale=surface_scale, kernel_unit_length=kernel_unit_length, lighting_color=lighting_color)

    @property
    def light(self) -> LightSource | None:
        """The light-source child, or None if there is none."""
        return next((c for c in self if isinstance(c, LightSource)), None)


class FeDiffuseLighting(_Lighting, tag="feDiffuseLighting"):
    """``<feDiffuseLighting>``: Lambertian lighting of the alpha bump map.

    Parameters
    ----------
    *light : LightSource
        The light source child.
    diffuse_constant : float, optional
        Diffuse reflection constant. Defaults to None.
    surface_scale : float, optional
        Height of the surface for full alpha. Defaults to None.
    kernel_unit_length : float or tuple of float, optional
        Surface normal sampling distance. Defaults to None.
    lighting_color : Color or str, optional
        Color of the light. Defaults to None.
    **kwargs
        Sub-region (``x``, ``y``, ``width``, ``height``), ``result``, ``in_``
        and other SVG attributes in Python spelling.

    See Also
    --------
    FeSpecularLighting : Specular highlights.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(svg.FeDiffuseLighting(svg.FeDistantLight(45, 60), surface_scale=2))
    '<feDiffuseLighting surfaceScale="2"><feDistantLight azimuth="45" elevation="60"/></feDiffuseLighting>'
    """

    def __init__(self, *light: Child, diffuse_constant: float | None = None, **kwargs: Any) -> None:
        super().__init__(*light, **kwargs)
        self.update(diffuse_constant=diffuse_constant)


class FeSpecularLighting(_Lighting, tag="feSpecularLighting"):
    """``<feSpecularLighting>``: Phong specular highlights.

    Parameters
    ----------
    *light : LightSource
        The light source child.
    specular_constant : float, optional
        Specular reflection constant. Defaults to None.
    specular_exponent : float, optional
        Shininess exponent. Defaults to None.
    surface_scale : float, optional
        Height of the surface for full alpha. Defaults to None.
    kernel_unit_length : float or tuple of float, optional
        Surface normal sampling distance. Defaults to None.
    lighting_color : Color or str, optional
        Color of the light. Defaults to None.
    **kwargs
        Sub-region (``x``, ``y``, ``width``, ``height``), ``result``, ``in_``
        and other SVG attributes in Python spelling.

    See Also
    --------
    FeDiffuseLighting : Diffuse lighting.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(svg.FeSpecularLighting(svg.FePointLight(1, 2, 3), specular_exponent=5))
    '<feSpecularLighting specularExponent="5"><fePointLight x="1" y="2" z="3"/></feSpecularLighting>'
    """

    def __init__(
        self,
        *light: Child,
        specular_constant: float | None = None,
        specular_exponent: float | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*light, **kwargs)
        self.update(specular_constant=specular_constant, specular_exponent=specular_exponent)
