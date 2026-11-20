"""
PostScript ``image`` and ``colorimage`` read into embedded pictures.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from ...transform.matrix import Matrix
from ._constants import (
    CHANNEL_MAX,
    CMYK_CHANNELS,
    GRAY_CHANNELS,
    MAX_IMAGE_CALLS,
    RGB_CHANNELS,
    SUPPORTED_BITS,
)
from ._eps_syntax import Literal, Procedure, _File, _Underflow
from ._pdf_content import _clip

if TYPE_CHECKING:
    from ._eps_machine import _Machine

__all__: list[str] = []


def _source_bytes(machine: _Machine, source: Any, need: int, depth: int) -> bytes:
    """Up to *need* bytes from an image data source: ``currentfile``, a string or a procedure returning strings."""
    if isinstance(source, _File):
        return machine.file_data[:need]
    if isinstance(source, bytes):
        return source[:need]
    if not isinstance(source, Procedure):
        return b""
    chunks: list[bytes] = []
    size = 0
    for _ in range(MAX_IMAGE_CALLS):
        before = len(machine.stack)
        machine.execute(source, depth + 1)
        if len(machine.stack) <= before or not isinstance(machine.stack[-1], bytes) or not machine.stack[-1]:
            break
        chunks.append(machine.stack.pop())
        size += len(chunks[-1])
        if size >= need:
            break
    return b"".join(chunks)[:need]


def _place_image(machine: _Machine, depth: int, operands: list[Any], sources: list[Any], channels: int) -> None:
    """Add an ``Image`` for 8-bit samples read from *sources* (one interleaved source, or one per channel)."""
    from ...elements.structure import Image

    width, height, bits, matrix = operands
    if int(bits) != SUPPORTED_BITS or not isinstance(matrix, list) or width < 1 or height < 1:
        raise _Underflow
    columns, rows = int(width), int(height)
    count = columns * rows
    if len(sources) == 1:
        data = _source_bytes(machine, sources[0], count * channels, depth)
        raw = np.frombuffer(data, np.uint8)
    else:
        planes = [np.frombuffer(_source_bytes(machine, s, count, depth), np.uint8) for s in sources]
        raw = np.dstack(planes).ravel() if len({p.size for p in planes}) == 1 else np.empty(0, np.uint8)
    if raw.size < count * channels:
        raise _Underflow
    samples = raw[:count * channels].reshape(rows, columns, channels).astype(np.float32) / CHANNEL_MAX
    if channels == GRAY_CHANNELS:
        rgb = np.repeat(samples, RGB_CHANNELS, axis=2)
    elif channels == CMYK_CHANNELS:
        c, m, y, k = (samples[..., i] for i in range(CMYK_CHANNELS))
        rgb = np.dstack([(1 - c) * (1 - k), (1 - m) * (1 - k), (1 - y) * (1 - k)])
    else:
        rgb = samples
    pixels = np.concatenate([rgb, np.ones((rows, columns, 1), np.float32)], axis=2)
    image = Image(pixels, 0, 0, columns, rows, preserve_aspect_ratio="none")
    image.t = machine.state.ctm @ Matrix(*(float(v) for v in matrix[:6])).inverse()
    if machine.state.clip:
        _clip(image, machine.state.clip)
    machine.shapes.append(image)


def _image(machine: _Machine, depth: int) -> None:
    """``image`` in its five-operand gray form."""
    operands = machine.pop(5, object)
    _place_image(machine, depth, operands[:4], operands[4:], GRAY_CHANNELS)


def _colorimage(machine: _Machine, depth: int) -> None:
    """``colorimage``: gray, RGB or CMYK samples from one source or one source per component."""
    channels = int(machine.pop(1)[0])
    multi = machine.pop(1, bool)[0]
    if channels not in (GRAY_CHANNELS, RGB_CHANNELS, CMYK_CHANNELS):
        raise _Underflow
    sources = machine.pop(channels if multi else 1, object)
    _place_image(machine, depth, machine.pop(4, object), sources, channels)


def _filter(machine: _Machine, _: int) -> None:
    """``filter``: the ASCII-hex data is decoded when read, so the source is returned unchanged."""
    machine.pop(1, Literal)
    machine.pop(1, object)
    machine.stack.append(_File())
