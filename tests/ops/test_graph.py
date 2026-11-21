import pytest

import svgwriter as svg

nx = pytest.importorskip("networkx")


def test_directed_graph_has_nodes_edges_arrows_and_labels():
    graph = nx.DiGraph([("a", "b"), ("b", "c"), ("c", "a"), ("a", "c")])
    graph.nodes["a"]["fill"] = "gold"
    picture = svg.ops.draw_graph(graph)
    edges, nodes = picture
    assert len([e for e in nodes if e.tag == "circle"]) == 3 and picture.root().get_element_by_id("node-a").get("fill") == "gold"
    assert len([e for e in edges if e.tag == "polygon"]) == 4 and len([e for e in edges if e.tag == "path"]) == 2
    assert [t.text_content for t in nodes if t.tag == "text"] == ["a", "b", "c"]


def test_layouts_positions_and_errors():
    graph = nx.path_graph(3)
    fixed = svg.ops.draw_graph(graph, layout={0: (0, 0), 1: (1, 0), 2: (2, 0)}, labels=False)
    xs = [c.get("cx") for c in fixed[1]]
    assert xs == sorted(xs) and len({c.get("cy") for c in fixed[1]}) == 1
    assert svg.ops.draw_graph(graph, layout="circular") is not None
    with pytest.raises(ValueError, match="layout"):
        svg.ops.draw_graph(graph, layout="nope")


def test_documents_accept_graphs_and_drawings_are_reproducible():
    doc = svg.Document()
    doc.add(nx.karate_club_graph())
    assert len(list(doc.root.iter("circle"))) == 34
    assert str(svg.ops.draw_graph(nx.karate_club_graph())) == str(svg.ops.draw_graph(nx.karate_club_graph()))


def test_edge_labels_show_weights_and_unknown_objects_are_refused():
    graph = nx.Graph()
    graph.add_edge("a", "b", weight=2.5)
    picture = svg.ops.draw_graph(graph, edge_labels=True)
    assert [t.text_content for t in picture[0] if t.tag == "text"] == ["2.5"]
    with pytest.raises(TypeError, match="networkx, igraph, rustworkx graph, not dict"):
        svg.ops.draw_graph({"a": ["b"]})
    with pytest.raises(ValueError, match="no position for node"):
        svg.ops.draw_graph(graph, layout={"a": (0, 0)})
