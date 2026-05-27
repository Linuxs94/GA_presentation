from __future__ import annotations

import math
import numpy as np


PointTuple = tuple[float, float]
PointLike = tuple[float, float] | object


def point_xy(point: PointLike) -> PointTuple:
    if hasattr(point, "x") and hasattr(point, "y"):
        return (float(point.x), float(point.y))
    return (float(point[0]), float(point[1]))


def polygon_edges(polygon: list[PointLike], closed: bool = True) -> list[tuple[PointTuple, PointTuple]]:
    if len(polygon) < 2:
        return []
    limit = len(polygon) if closed else len(polygon) - 1
    return [
        (point_xy(polygon[index]), point_xy(polygon[(index + 1) % len(polygon)]))
        for index in range(limit)
    ]


def winding_number(point: PointLike, polygon: list[PointLike], closed: bool = True) -> float:
    px, py = point_xy(point)
    total_angle = 0.0
    for start, end in polygon_edges(polygon, closed=closed):
        x1 = start[0] - px
        y1 = start[1] - py
        x2 = end[0] - px
        y2 = end[1] - py
        total_angle += math.atan2(x1 * y2 - y1 * x2, x1 * x2 + y1 * y2)
    return total_angle / (2.0 * math.pi)


def winding_trace(
    point: PointLike,
    polygon: list[PointLike],
    closed: bool = True,
) -> list[dict[str, object]]:
    px, py = point_xy(point)
    total_angle = 0.0
    steps: list[dict[str, object]] = []
    for index, (start, end) in enumerate(polygon_edges(polygon, closed=closed)):
        x1 = start[0] - px
        y1 = start[1] - py
        x2 = end[0] - px
        y2 = end[1] - py
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


def WN_compute_bounds(polygons: list[list[PointLike]], margin: float = 2.0) -> tuple[float, float, float, float]:
    all_x = [point_xy(point)[0] for polygon in polygons for point in polygon]
    all_y = [point_xy(point)[1] for polygon in polygons for point in polygon]
    return min(all_x) - margin, max(all_x) + margin, min(all_y) - margin, max(all_y) + margin


def build_winding_field(
    polygon: list[PointLike],
    bounds: tuple[float, float, float, float],
    resolution: int = 220,
    discrete: bool = False,
    closed: bool = True,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:

    #cluster center
    min_x, max_x, min_y, max_y = bounds
    xs = np.linspace(min_x, max_x, resolution)
    ys = np.linspace(min_y, max_y, resolution)
    field = np.zeros((resolution, resolution))

    # computer cluster center
    poly_pts = [point_xy(pt) for pt in polygon]
    cx = float(np.mean([pt[0] for pt in poly_pts])) if poly_pts else 0.0
    cy = float(np.mean([pt[1] for pt in poly_pts])) if poly_pts else 0.0

    for row, y in enumerate(ys):
        for column, x in enumerate(xs):
            # translate point and poligon
            target_point = (x - cx, y - cy)
            translated_polygon = [(pt[0] - cx, pt[1] - cy) for pt in poly_pts]
            
            winding = winding_number(target_point, translated_polygon, closed=closed)
            field[row, column] = 1.0 if discrete and abs(winding) > 0.5 else winding

    return field, xs, ys
