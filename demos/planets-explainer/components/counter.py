"""A mechanical counter: one wheel of digits per place, rolling like an odometer."""

import svgwriter as svg


class Counter:
    """*places* digit wheels at (x, y), each showing one digit through a window *size* tall.

    :meth:`show` turns the wheels to a value; a higher wheel turns only while the wheel below it rolls
    from 9 to 0, as on an odometer.
    """

    def __init__(self, doc: svg.Document, *, x: float, y: float, places: int, size: float) -> None:
        self.size = size
        width = size * 0.62
        window = doc.clip_path(svg.rect(x, y - size, width * places, size * 1.2))
        self.group = doc.group(clip_path=window)
        self.wheels = []
        for place in range(places):
            wheel = svg.Group()
            for digit in range(11):
                wheel += svg.text(str(digit % 10), x=x + width * (places - 1 - place), y=y + digit * size,
                                  font_size=size).as_role("title")
            self.group += wheel
            self.wheels.append(wheel)

    def show(self, value: float) -> None:
        """Turn the wheels to *value*; fractions roll the lowest wheel part of the way."""
        for place, wheel in enumerate(self.wheels):
            unit = 10 ** place
            position = value // unit % 10
            below = value % unit
            position += min(max(below - (unit - 1), 0.0), 1.0) if place else value % 1
            wheel.t = svg.Matrix.translate(0, -position * self.size)
