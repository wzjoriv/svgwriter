import pytest

import svgwriter as svg


def _circles(picture):
    return [c for c in picture[1] if c.tag == "circle"]


def _texts(group):
    return [t.text_content for t in group if t.tag == "text"]


def test_igraph_names_attributes_direction_and_layouts():
    ig = pytest.importorskip("igraph")
    graph = ig.Graph([(0, 1), (1, 2), (2, 1)], directed=True)
    graph.vs["name"] = ["a", "b", "c"]
    graph.vs["fill"] = ["gold", None, None]
    graph.es["weight"] = [1, 2, 3]
    graph.es["stroke"] = ["red", None, None]
    picture = svg.ops.draw_graph(graph, edge_labels=True)
    assert picture.root().get_element_by_id("node-a").get("fill") == "gold"
    assert _texts(picture[1]) == ["a", "b", "c"] and _texts(picture[0]) == ["1", "2", "3"]
    assert len([e for e in picture[0] if e.tag == "polygon"]) == 3
    assert len([e for e in picture[0] if e.tag == "path"]) == 2
    assert picture[0][0].get("stroke") == "red"
    for layout in ("circular", "kamada_kawai", "sugiyama", "reingold_tilford", graph.layout("grid")):
        assert len(_circles(svg.ops.draw_graph(graph, layout=layout))) == 3
    assert str(svg.ops.draw_graph(graph)) == str(svg.ops.draw_graph(graph))
    with pytest.raises(ValueError, match="unknown igraph layout 'spectral'"):
        svg.ops.draw_graph(graph, layout="spectral")


def test_igraph_without_names_is_keyed_by_index_and_documents_take_it():
    ig = pytest.importorskip("igraph")
    graph = ig.Graph.Famous("Zachary")
    doc = svg.Document()
    doc.add(graph)
    assert len(list(doc.root.iter("circle"))) == graph.vcount()
    fixed = svg.ops.draw_graph(ig.Graph([(0, 1)]), layout={0: (0, 0), 1: (1, 0)}, labels=False)
    assert fixed.root().get_element_by_id("node-1") is not None and not graph.is_directed()


def test_rustworkx_payloads_direction_and_layouts():
    rx = pytest.importorskip("rustworkx")
    graph = rx.PyDiGraph()
    a, b, c = graph.add_node({"label": "start", "fill": "gold"}), graph.add_node("middle"), graph.add_node(None)
    graph.add_edges_from([(a, b, 4), (b, c, {"label": "go", "stroke": "red"}), (c, b, None)])
    picture = svg.ops.draw_graph(graph, edge_labels=True)
    assert picture.root().get_element_by_id("node-0").get("fill") == "gold"
    assert _texts(picture[1]) == ["start", "middle", "2"] and _texts(picture[0]) == ["4", "go"]
    assert len([e for e in picture[0] if e.tag == "polygon"]) == 3
    for layout in ("circular", "spiral", "shell", "random", rx.spring_layout):
        assert len(_circles(svg.ops.draw_graph(graph, layout=layout))) == 3
    assert str(svg.ops.draw_graph(graph)) == str(svg.ops.draw_graph(graph))
    with pytest.raises(ValueError, match="unknown rustworkx layout"):
        svg.ops.draw_graph(graph, layout="planar")


def test_rustworkx_undirected_graphs_have_no_arrows_and_documents_take_them():
    rx = pytest.importorskip("rustworkx")
    graph = rx.generators.cycle_graph(5)
    doc = svg.Document()
    doc.add(graph)
    assert len(list(doc.root.iter("circle"))) == 5 and not list(doc.root.iter("polygon"))
    assert svg.ops.graph.is_graph(graph) and not svg.ops.graph.is_graph(rx)
