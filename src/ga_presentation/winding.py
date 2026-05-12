from __future__ import annotations

import math
import numpy as np


PointTuple = tuple[float, float]


def polygon_edges(polygon: list[PointTuple], closed: bool = True) -> list[tuple[PointTuple, PointTuple]]:
    if len(polygon) < 2:
        return []
    limit = len(polygon) if closed else len(polygon) - 1
    return [
        (polygon[index], polygon[(index + 1) % len(polygon)])
        for index in range(limit)
    ]


def winding_number(point: PointTuple, polygon: list[PointTuple], closed: bool = True) -> float:
    total_angle = 0.0
    for start, end in polygon_edges(polygon, closed=closed):
        x1 = start[0] - point[0]
        y1 = start[1] - point[1]
        x2 = end[0] - point[0]
        y2 = end[1] - point[1]
        total_angle += math.atan2(x1 * y2 - y1 * x2, x1 * x2 + y1 * y2)
    return total_angle / (2.0 * math.pi)


def winding_trace(
    point: PointTuple,
    polygon: list[PointTuple],
    closed: bool = True,
) -> list[dict[str, object]]:
    total_angle = 0.0
    steps: list[dict[str, object]] = []
    for index, (start, end) in enumerate(polygon_edges(polygon, closed=closed)):
        x1 = start[0] - point[0]
        y1 = start[1] - point[1]
        x2 = end[0] - point[0]
        y2 = end[1] - point[1]
        angle = math.atan2(x1 * y2 - y1 * x2, x1 * x2 + y1 * y2)
        total_angle += angle
        steps.append(
            {
                "edge_index": index,
                "start": start,
                "end": end,
                "angle": angle / (2.0 * math.pi),
                "winding": total_angle / (2.0 * math.pi),
            }
        )
    return steps


def compute_bounds(polygons: list[list[PointTuple]], margin: float = 2.0) -> tuple[float, float, float, float]:
    all_x = [point[0] for polygon in polygons for point in polygon]
    all_y = [point[1] for polygon in polygons for point in polygon]
    return min(all_x) - margin, max(all_x) + margin, min(all_y) - margin, max(all_y) + margin


def build_winding_field(
    polygon: list[PointTuple],
    bounds: tuple[float, float, float, float],
    resolution: int = 220,
    discrete: bool = False,
    closed: bool = True,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    min_x, max_x, min_y, max_y = bounds
    xs = np.linspace(min_x, max_x, resolution)
    ys = np.linspace(min_y, max_y, resolution)
    field = np.zeros((resolution, resolution))

    for row, y in enumerate(ys):
        for column, x in enumerate(xs):
            winding = winding_number((x, y), polygon, closed=closed)
            field[row, column] = 1.0 if discrete and abs(winding) > 0.5 else winding

    return field, xs, ys
