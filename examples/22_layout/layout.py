"""# Layout

You will build: a calculator whose keys, keypad and card size themselves, so changing one setting re-lays out
the whole design.

Run it from this folder with ``python layout.py``, or open ``layout.ipynb``.
"""

import svgwriter as svg

# %% [markdown]
# A key is a `VStack` holding one label, centred, with padding and a rounded background. The background
# is sized to the stack, whatever the label.

# %%
OPERATORS = "÷×−+="


def key(label: str) -> svg.VStack:
    """One calculator key: the label on a rounded rect, in the accent role for operators."""
    role = "accent" if label in OPERATORS else "box"
    return svg.VStack(svg.text(label, font_size=20).as_role("text"), padding=(12, 16), align="center",
                      background=svg.rect(0, 0, 1, 1, rx=10).as_role(role))


seven = key("7")
seven

# %% [markdown]
# The keypad is a `Grid` of four equal columns. `"1fr"` columns without a fixed width take the widest key,
# so every key comes out the same size, and the default `"stretch"` sizes each key to its cell. The zero
# key spans two columns.

# %%
labels = ["C", "±", "%", "÷", "7", "8", "9", "×", "4", "5", "6", "−", "1", "2", "3", "+", "0", ".", "="]
keys = [key(label) for label in labels]
keypad = svg.Grid(*keys, columns=4, gap=8)
keypad.span(keys[labels.index("0")], columns=2)
keypad

# %% [markdown]
# The card stacks a display above the keypad. In the display a `Spacer` pushes the number to the right
# edge, and `align="stretch"` makes the display as wide as the keypad.

# %%
display = svg.HStack(svg.Spacer(), svg.text("1,234.5", font_size=32).as_role("title"),
                     padding=(10, 14), background=svg.rect(0, 0, 1, 1, rx=10).as_role("surface"))
card = svg.VStack(display, keypad, gap=12, padding=16, align="stretch",
                  background=svg.rect(0, 0, 1, 1, rx=20).as_role("background"))
doc = svg.Document(theme="dark")
doc += card
doc.save("22_calculator.svg")
doc

# %% [markdown]
# One setting re-lays out everything: a wider gap moves the keys and grows the keypad, the display and the card.

# %%
keypad.gap = 14
card.padding = 24
doc.save("22_calculator_roomy.svg")
doc

# %% [markdown]
# Changing content works the same way: a longer number widens the display and the card follows.
# Next: [23 Widgets](../23_widgets/widgets.py).

# %%
display[2].text_content = "3.14159265358979"
doc.save("22_calculator.pdf")
doc
