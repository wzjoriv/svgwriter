"""``press``: dip a key as if a finger pressed it, then let it spring back."""

import svgwriter as svg


@svg.preset.animation
def press(motion: svg.Motion, *, depth: float = 3, dur: float = 0.25, begin: float = 0) -> svg.Motion:
    """Move down by *depth* and back over *dur* seconds, once."""
    motion.element.append(svg.AnimateTransform("translate", attribute_name="transform", additive="sum",
                                               values=f"0 0;0 {depth:g};0 0", dur=dur, begin=begin))
    return motion
