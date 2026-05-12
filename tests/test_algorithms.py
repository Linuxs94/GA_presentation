from algorithms import (
    bowyer_watson,
    graham_scan,
    grid_difference,
    grid_intersection,
    grid_union,
    marching_squares,
    point_in_polygon,
    prune_triangles_to_polygon,
    rasterize_polygon,
)
from datasets import default_primitive_datasets


def test_graham_scan_returns_outer_hull():
    points = [(0, 0), (2, 0), (2, 2), (0, 2), (1, 1)]
    hull, _ = graham_scan(points)
    assert set(hull) == {(0, 0), (2, 0), (2, 2), (0, 2)}


def test_point_in_polygon_matches_star_center():
    star = default_primitive_datasets()["star"]
    assert point_in_polygon((0.0, 0.0), star) is True
    assert point_in_polygon((6.0, 6.0), star) is False


def test_grid_boolean_relations():
    a = [[1, 0], [1, 1]]
    b = [[0, 1], [1, 0]]
    assert grid_union(a, b) == [[1, 1], [1, 1]]
    assert grid_intersection(a, b) == [[0, 0], [1, 0]]
    assert grid_difference(a, b) == [[1, 0], [0, 1]]


def test_marching_squares_emits_segments_for_simple_block():
    grid = [
        [1, 1],
        [1, 0],
    ]
    segments, _ = marching_squares(grid, (0.0, 2.0, 0.0, 2.0))
    assert len(segments) > 0


def test_delaunay_and_pruning_keep_inner_mesh():
    star = default_primitive_datasets()["star"]
    points = star + [(-1.0, 0.0), (1.0, 0.0), (0.0, 1.0)]
    triangles, _ = bowyer_watson(points)
    kept = prune_triangles_to_polygon(triangles, star)
    assert len(triangles) >= len(kept) > 0


def test_rasterize_polygon_marks_center_inside():
    square = default_primitive_datasets()["square"]
    binary, _, _ = rasterize_polygon(square, (-5.0, 5.0, -5.0, 5.0), 10, 10)
    assert any(any(cell for cell in row) for row in binary)
