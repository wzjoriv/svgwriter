"""``deal``: slide in from above and settle, once."""

import svgwriter as svg


@svg.preset.animation
def deal(motion: svg.Motion, *, drop: float = 40, dur: float = 0.8, begin: float = 0) -> svg.Motion:
    """Fall *drop* units into place over *dur* seconds while fading in, and stay there."""
    element = motion.element
    element.append(svg.AnimateTransform("translate", attribute_name="transform", additive="sum",
                                        values=f"0 {-drop:g};0 0", dur=dur, begin=begin, fill="freeze",
                                        ease="ease-out"))
    element.append(svg.Animate(attribute_name="opacity", values="0;1", dur=dur, begin=begin, fill="freeze"))
    return motion
