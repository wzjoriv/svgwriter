"""``twinkle``: dim and brighten, again and again."""

import svgwriter as svg


@svg.preset.animation
def twinkle(motion: svg.Motion, *, low: float = 0.3, dur: float = 2.5, begin: float = 0) -> svg.Motion:
    """Fade to *low* opacity and back over *dur* seconds, forever."""
    motion.element.append(svg.Animate(attribute_name="opacity", values=f"1;{low:g};1", dur=dur, begin=begin,
                                      repeat_count="indefinite"))
    return motion
