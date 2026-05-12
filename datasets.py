from __future__ import annotations

import math
from pathlib import Path


Point = tuple[float, float]


def read_polygon(path: str | Path) -> list[Point]:
    points: list[Point] = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            x_text, y_text = line.strip().split()
            points.append((float(x_text), float(y_text)))
    return points


def regular_polygon(
    center: Point,
    radius: float,
    sides: int,
    angle_offset: float = 0.0,
) -> list[Point]:
    points: list[Point] = []
    for index in range(sides):
        angle = angle_offset + (2.0 * math.pi * index) / sides
        x = center[0] + radius * math.cos(angle)
        y = center[1] + radius * math.sin(angle)
        points.append((x, y))
    return points


def star_polygon(
    center: Point,
    inner_radius: float,
    outer_radius: float,
    arms: int,
    angle_offset: float = -math.pi / 2.0,
) -> list[Point]:
    points: list[Point] = []
    for index in range(arms * 2):
        radius = outer_radius if index % 2 == 0 else inner_radius
        angle = angle_offset + (math.pi * index) / arms
        x = center[0] + radius * math.cos(angle)
        y = center[1] + radius * math.sin(angle)
        points.append((x, y))
    return points


def default_primitive_datasets() -> dict[str, list[Point]]:
    return {
        "square": regular_polygon((0.0, 0.0), 4.0, 4, angle_offset=math.pi / 4.0),
        "hexagon": regular_polygon((0.0, 0.0), 4.5, 6, angle_offset=math.pi / 6.0),
        "star": star_polygon((0.0, 0.0), 2.2, 5.0, 5),
    }


def cf_assignment_polygons(root: str | Path) -> tuple[list[Point], list[Point]]:
    root_path = Path(root)
    return read_polygon(root_path / "p1.txt"), read_polygon(root_path / "p2.txt")
