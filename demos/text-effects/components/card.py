"""A dark card with a faint border, a few stars and a caption."""

import random

import svgwriter as svg

STARS = 40           # stars scattered over the card
STAR_SEED = 7        # the same sky on every build


def card(width: float, height: float, *, inset: float, caption: str) -> svg.Group:
    """The card filling (inset, inset) to (width - inset, height - inset), with *caption* in its corner."""
    group = svg.Group()
    group += svg.rect(0, 0, width, height).as_role("background")
    group += svg.rect(inset, inset, width - 2 * inset, height - 2 * inset, rx=18).as_role("box")
    sky = random.Random(STAR_SEED)
    with svg.Group(fill="#ffffff") as stars:
        for _ in range(STARS):
            stars += svg.circle(sky.uniform(inset, width - inset), sky.uniform(inset, height - inset),
                                sky.uniform(0.4, 1.3), opacity=sky.uniform(0.15, 0.5))
    group += stars
    group += svg.text(caption, x=width - inset - 20, y=height - inset - 16, text_anchor="end").as_role("caption")
    return group
