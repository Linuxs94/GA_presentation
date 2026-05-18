from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ga_presentation.convex_hull import monotone_chain
from ga_presentation.datasets import regular_polygon
from ga_presentation.fortune import compute_voronoi
from ga_presentation.structures import Point
from ga_presentation.winding import build_winding_field, winding_number


def test_monotone_chain_keeps_outer_points():
    points = [(0, 0), (2, 0), (2, 2), (0, 2), (1, 1)]
    hull, snapshots = monotone_chain(points)
    assert {tuple(point) for point in hull} == {(0, 0), (2, 0), (2, 2), (0, 2)}
    assert len(snapshots) > 0


def test_winding_number_inside_and_outside():
    square = regular_polygon((0.0, 0.0), 4.0, 4)
    assert abs(winding_number((0.0, 0.0), square)) > 0.5
    assert abs(winding_number((8.0, 8.0), square)) < 0.5


def test_closed_and_open_winding_differ():
    star = regular_polygon((0.0, 0.0), 4.0, 5)
    closed_value = abs(winding_number((0.0, 0.0), star, closed=True))
    open_value = abs(winding_number((0.0, 0.0), star, closed=False))
    assert closed_value > open_value


def test_winding_accepts_point_objects():
    square = [Point(-1.0, -1.0), Point(1.0, -1.0), Point(1.0, 1.0), Point(-1.0, 1.0)]
    assert abs(winding_number(Point(0.0, 0.0), square)) > 0.5


def test_winding_field_builds_nonzero_samples():
    square = regular_polygon((0.0, 0.0), 4.0, 4)
    field, _, _ = build_winding_field(square, (-5.0, 5.0, -5.0, 5.0), resolution=40)
    assert field.shape == (40, 40)
    assert field.max() > 0.5


def test_fortune_produces_snapshots_and_edges():
    points = [(1.0, 1.0), (3.0, 2.0), (2.0, 4.0), (5.0, 3.0), (4.0, 1.5)]
    voronoi = compute_voronoi(points, (0.0, 6.0, 0.0, 5.0), capture=True)
    assert len(voronoi.snapshots) > 0
    assert any(snapshot.finished_segments for snapshot in voronoi.snapshots)
    assert any(snapshot.active_segments for snapshot in voronoi.snapshots[:-1])
