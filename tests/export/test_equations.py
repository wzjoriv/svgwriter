import io
import zipfile

import pytest
from lxml import etree

import svgwriter as svg

pytest.importorskip("latex2mathml")
from svgwriter.formats.export._office._omml import latex_to_omml  # noqa: E402

M = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"
ORDER = {
    "oMathPara": ["oMathParaPr", "oMath"],
    "f": ["fPr", "num", "den"],
    "fPr": ["type", "ctrlPr"],
    "sSup": ["sSupPr", "e", "sup"],
    "sSub": ["sSubPr", "e", "sub"],
    "sSubSup": ["sSubSupPr", "e", "sub", "sup"],
    "rad": ["radPr", "deg", "e"],
    "radPr": ["degHide", "ctrlPr"],
    "nary": ["naryPr", "sub", "sup", "e"],
    "naryPr": ["chr", "limLoc", "grow", "subHide", "supHide", "ctrlPr"],
    "d": ["dPr", "e"],
    "dPr": ["begChr", "sepChr", "endChr", "grow", "shp", "ctrlPr"],
    "acc": ["accPr", "e"],
    "accPr": ["chr", "ctrlPr"],
    "bar": ["barPr", "e"],
    "barPr": ["pos", "ctrlPr"],
    "groupChr": ["groupChrPr", "e"],
    "groupChrPr": ["chr", "pos", "vertJc", "ctrlPr"],
    "limLow": ["limLowPr", "e", "lim"],
    "limUpp": ["limUppPr", "e", "lim"],
    "m": ["mPr", "mr"],
    "mr": ["e"],
    "r": ["rPr", "*rPr", "t"],
    "rPr": ["lit", "nor", "sty", "brk", "aln"],
}
REQUIRED = {"f": {"num", "den"}, "sSup": {"e", "sup"}, "sSub": {"e", "sub"}, "sSubSup": {"e", "sub", "sup"},
            "rad": {"deg", "e"}, "nary": {"sub", "sup", "e"}, "d": {"e"}, "acc": {"e"}, "bar": {"e"},
            "limLow": {"e", "lim"}, "limUpp": {"e", "lim"}, "m": {"mr"}, "oMathPara": {"oMath"}}
ARGUMENTS = {"oMath", "e", "num", "den", "sub", "sup", "deg", "lim"}
CONTENT = {"r", "f", "sSup", "sSub", "sSubSup", "rad", "nary", "d", "acc", "bar", "groupChr", "limLow", "limUpp",
           "m", "func", "box", "borderBox", "sPre", "eqArr", "phant"}


def _local(element):
    namespace, _, name = element.tag[1:].partition("}")
    return name if namespace == M[1:-1] else "*" + name


def _check(element):
    """Children follow the OMML schema order of ECMA-376 shared-math.xsd and required parts are present."""
    name = _local(element)
    names = [_local(child) for child in element]
    if name in ARGUMENTS:
        assert set(names) <= CONTENT, (name, names)
    elif name in ORDER:
        positions = [ORDER[name].index(child) if child in ORDER[name] else -1 for child in names]
        assert -1 not in positions and positions == sorted(positions), (name, names)
        assert REQUIRED.get(name, set()) <= set(names), (name, names)
    if name == "rPr":
        assert not ({"nor", "sty"} <= set(names))
    for child in element:
        if _local(child) not in ("*rPr",):
            _check(child)


SOURCES = [r"\frac{a}{b} + x^2", r"\sum_{i=1}^{n} i^2", r"\int_0^1 x\,dx", r"\sqrt[3]{x} + \sqrt{y}",
           r"\left( \frac{1}{2} \right]", r"\hat{x} \sin\theta", r"\begin{matrix} 1 & 2 \\ 3 & 4 \end{matrix}",
           r"\text{if } x_i^2", r"\lim_{x \to 0} f", r"\overline{ab} + \underline{c}", r"\binom{n}{k}",
           r"\prod_k a_k", r"\overbrace{a+b}", r"$e^{i\pi} + 1 = 0$"]


@pytest.mark.parametrize("source", SOURCES)
def test_omml_follows_the_schema(source):
    root = etree.fromstring(latex_to_omml(source))
    assert root.tag == M + "oMathPara" and root[0].tag == M + "oMath"
    _check(root)


def test_omml_maps_the_common_constructs():
    def tags(source):
        return {_local(e) for e in etree.fromstring(latex_to_omml(source)).iter()}

    assert {"f", "num", "den"} <= tags(r"\frac{a}{b}")
    assert "nary" in tags(r"\sum_{i=1}^n i") and "nary" in tags(r"\int_0^1 x")
    assert "rad" in tags(r"\sqrt{x}") and "deg" in tags(r"\sqrt[3]{x}")
    assert "d" in tags(r"\left( x \right)") and "m" in tags(r"\begin{matrix}1&2\end{matrix}")
    assert "acc" in tags(r"\hat{x}") and "bar" in tags(r"\overline{x}") and "limLow" in tags(r"\lim_{x\to0}")
    assert "sSubSup" in tags("x_i^2")
    noBar = etree.fromstring(latex_to_omml(r"\binom{n}{k}")).find(f".//{M}type")
    assert noBar.get(M + "val") == "noBar"


def test_unconvertible_source_raises_value_error():
    with pytest.raises(ValueError):
        latex_to_omml(r"\frac{1}")


def _formula_doc():
    doc = svg.Document(300, 120)
    doc.rect(5, 5, 50, 50, fill="red")
    doc.add(svg.latex(r"\frac{a}{b} + x^2", engine="mathtext")).scale(2).place(150, 60)
    return doc


def test_latex_remembers_its_source():
    group = svg.latex("x^2", engine="mathtext", display=True)
    assert group.get("data-latex") == "x^2" and float(group.get("data-latex-size")) == pytest.approx(12)
    doc = svg.Document(10, 10)
    doc.add(group)
    again = svg.Document.from_string(doc.to_string())
    assert again[0].get("data-latex") == "x^2"


def test_pptx_writes_an_editable_equation_where_the_formula_was():
    pptx = pytest.importorskip("pptx")
    data = svg.export.export(_formula_doc(), "pptx")
    deck = pptx.Presentation(io.BytesIO(data))
    shapes = list(deck.slides[0].shapes)
    assert [s.name for s in shapes] == ["Rectangle 1", "Equation"]
    box = shapes[1]
    assert box.left / 9525 == pytest.approx(150 - box.width / 9525 / 2, abs=1)
    slide = etree.fromstring(zipfile.ZipFile(io.BytesIO(data)).read("ppt/slides/slide1.xml"))
    math = slide.find(".//{http://schemas.microsoft.com/office/drawing/2010/main}m")
    assert math is not None and math[0].tag == M + "oMathPara"
    _check(math[0])
    size = math.find(".//{http://schemas.openxmlformats.org/drawingml/2006/main}rPr").get("sz")
    assert int(size) == 1500
    back = svg.FORMATS.reader("pptx").read(data)
    assert [e.tag for e in back] == ["path", "g"] and back[1][0].text_content == "ab+x2"


def test_pptx_falls_back_to_outlines_when_the_source_does_not_convert():
    pptx = pytest.importorskip("pptx")
    doc = svg.Document(100, 50)
    group = doc.add(svg.latex("x", engine="mathtext"))
    group.set("data-latex", r"\frac{1}")
    shapes = list(pptx.Presentation(io.BytesIO(svg.export.export(doc, "pptx"))).slides[0].shapes)
    assert shapes and all(s.name != "Equation" for s in shapes)


def test_docx_floats_equations_over_the_shapes():
    docx = pytest.importorskip("docx")
    data = svg.export.export(_formula_doc(), "docx")
    docx.Document(io.BytesIO(data))
    body = etree.fromstring(zipfile.ZipFile(io.BytesIO(data)).read("word/document.xml"))
    paras = body.findall(f".//{M}oMathPara")
    assert len(paras) == 1
    _check(paras[0])
    wp = "{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}"
    anchors = body.findall(f".//{wp}anchor")
    assert not body.findall(f".//{wp}inline") and len(anchors) == 2
    equation = next(a for a in anchors if a.find(f"{wp}docPr").get("name").startswith("Equation"))
    offset = equation.find(f"{wp}positionH/{wp}posOffset")
    assert int(offset.text) / 9525 == pytest.approx(150 - 0.5 * int(equation.find(f"{wp}extent").get("cx"))
                                                    / 9525, abs=1)
    back = svg.FORMATS.reader("docx").read(data)
    assert [e.tag for e in back] == ["path", "g"] and "x" in back[1][0].text_content


def test_docx_with_only_a_formula_writes_an_equation_paragraph():
    docx = pytest.importorskip("docx")
    doc = svg.Document(100, 40)
    doc.add(svg.latex("a^2 + b^2 = c^2", engine="mathtext"))
    data = svg.export.export(doc, "docx")
    out = docx.Document(io.BytesIO(data))
    assert not out.inline_shapes
    paragraph = out.paragraphs[0]._p
    assert paragraph[0].tag == M + "oMathPara"
    _check(paragraph[0])
