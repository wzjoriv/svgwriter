import re

import svgwriter as svg


def test_a_paint_shared_by_two_documents_is_written_in_both():
    hatch = svg.patterns.hatch(gap=2, width=0.5)
    gradient = svg.LinearGradient.horizontal("red", "blue")
    texts = []
    for _ in range(2):
        doc = svg.Document(width=20, height=10)
        doc.rect(0, 0, 10, 10, fill=hatch)
        doc.rect(10, 0, 10, 10, fill=gradient)
        texts.append(doc.to_string())
    for text in texts:
        defined = set(re.findall(r'<(?:pattern|linearGradient) id="([^"]+)"', text))
        used = set(re.findall(r"url\(#([^)]+)\)", text))
        assert used and used <= defined
