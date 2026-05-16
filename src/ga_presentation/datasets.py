from __future__ import annotations

from pathlib import Path
import math
import random

from .structures import Point

PointTuple = tuple[float, float]
PointLike = Point | PointTuple


def read_polygon(path: str | Path) -> list[Point]:
    polygon: list[Point] = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            x_text, y_text = line.strip().split()
            polygon.append(Point(float(x_text), float(y_text)))
    return polygon


def load_repo_polygons(root: str | Path) -> dict[str, list[Point]]:
    root_path = Path(root)
    return {
        "p1": read_polygon(root_path / "p1.txt"),
        "p2": read_polygon(root_path / "p2.txt"),
        "p3": read_polygon(root_path / "p3.txt"),
        "p4": read_polygon(root_path / "p4.txt"),
    }


def regular_polygon(center: PointLike, radius: float, sides: int, angle_offset: float = 0.0) -> list[Point]:
    points: list[Point] = []
    for index in range(sides):
        angle = angle_offset + (2.0 * math.pi * index) / sides
        points.append(Point(center[0] + radius * math.cos(angle), center[1] + radius * math.sin(angle)))
    return points


def star_polygon(
    center: PointLike,
    inner_radius: float,
    outer_radius: float,
    arms: int,
    angle_offset: float = -math.pi / 2.0,
) -> list[Point]:
    points: list[Point] = []
    for index in range(arms * 2):
        radius = outer_radius if index % 2 == 0 else inner_radius
        angle = angle_offset + (math.pi * index) / arms
        points.append(Point(center[0] + radius * math.cos(angle), center[1] + radius * math.sin(angle)))
    return points


def sample_uniform_points(
    count: int,
    bounds: tuple[float, float, float, float],
    seed: int = 7,
) -> list[Point]:
    generator = random.Random(seed)
    min_x, max_x, min_y, max_y = bounds
    return [
        Point(generator.uniform(min_x, max_x), generator.uniform(min_y, max_y))
        for _ in range(count)
    ]


def sample_gaussian_clusters(
    count: int,
    centers: list[PointLike],
    sigma: float,
    seed: int = 11,
) -> list[Point]:
    generator = random.Random(seed)
    points: list[Point] = []
    for index in range(count):
        center = centers[index % len(centers)]
        points.append(Point(generator.gauss(center[0], sigma), generator.gauss(center[1], sigma)))
    return points


def sample_polygon_boundary(
    polygon: list[PointLike],
    count: int,
    seed: int = 19,
) -> list[Point]:
    generator = random.Random(seed)
    edges: list[tuple[PointLike, PointLike, float]] = []
    total_length = 0.0

    for index in range(len(polygon)):
        start = polygon[index]
        end = polygon[(index + 1) % len(polygon)]
        length = math.dist(start, end)
        total_length += length
        edges.append((start, end, total_length))

    points: list[Point] = []
    for _ in range(count):
        target = generator.uniform(0.0, total_length)
        for start, end, cumulative in edges:
            if target <= cumulative:
                previous = cumulative - math.dist(start, end)
                local_t = (target - previous) / max(math.dist(start, end), 1e-9)
                points.append(Point(start[0] + (end[0] - start[0]) * local_t, start[1] + (end[1] - start[1]) * local_t))
                break
    return points
