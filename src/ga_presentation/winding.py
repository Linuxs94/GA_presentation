
from __future__ import annotations

from dataclasses import dataclass
import math
import numpy as np


PointTuple = tuple[float, float]
PointLike = tuple[float, float] | object


@dataclass(frozen=True)
class WindingContribution:
    edge_index: int
    start: PointTuple
    end: PointTuple
    start_translated: PointTuple
    end_translated: PointTuple
    query_point_original: PointTuple
    query_point_translated: PointTuple
    polygon_center: PointTuple
    vector_start: PointTuple
    vector_end: PointTuple
    cross: float
    dot: float
    angle_radians: float
    angle: float
    winding_before: float
    winding_after: float
    closed: bool


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


def polygon_center(polygon: list[PointLike]) -> PointTuple:
    poly_pts = [point_xy(pt) for pt in polygon]
    if not poly_pts:
        return (0.0, 0.0)
    return (
        float(np.mean([pt[0] for pt in poly_pts])),
        float(np.mean([pt[1] for pt in poly_pts])),
    )


def translated_winding_setup(point: PointLike, polygon: list[PointLike]) -> dict[str, object]:
    original_point = point_xy(point)
    center = polygon_center(polygon)
    original_polygon = [point_xy(pt) for pt in polygon]
    translated_point = (original_point[0] - center[0], original_point[1] - center[1])
    translated_polygon = [(pt[0] - center[0], pt[1] - center[1]) for pt in original_polygon]
    return {
        "polygon_center": center,
        "query_point_original": original_point,
        "query_point_translated": translated_point,
        "polygon_original": original_polygon,
        "polygon_translated": translated_polygon,
    }


def winding_contributions(
    point: PointLike,
    polygon: list[PointLike],
    closed: bool = True,
) -> list[WindingContribution]:
    setup = translated_winding_setup(point, polygon)
    center = setup["polygon_center"]
    original_point = setup["query_point_original"]
    translated_point = setup["query_point_translated"]
    original_polygon = setup["polygon_original"]
    translated_polygon = setup["polygon_translated"]

    total_angle = 0.0
    contributions: list[WindingContribution] = []
    for index, ((start, end), (start_t, end_t)) in enumerate(
        zip(polygon_edges(original_polygon, closed=closed), polygon_edges(translated_polygon, closed=closed))
    ):
        x1 = start_t[0] - translated_point[0]
        y1 = start_t[1] - translated_point[1]
        x2 = end_t[0] - translated_point[0]
        y2 = end_t[1] - translated_point[1]
        cross = x1 * y2 - y1 * x2
        dot = x1 * x2 + y1 * y2
        angle_radians = math.atan2(cross, dot)
        winding_before = total_angle / (2.0 * math.pi)
        total_angle += angle_radians
        winding_after = total_angle / (2.0 * math.pi)
        contributions.append(
            WindingContribution(
                edge_index=index,
                start=start,
                end=end,
                start_translated=start_t,
                end_translated=end_t,
                query_point_original=original_point,
                query_point_translated=translated_point,
                polygon_center=center,
                vector_start=(x1, y1),
                vector_end=(x2, y2),
                cross=cross,
                dot=dot,
                angle_radians=angle_radians,
                angle=angle_radians / (2.0 * math.pi),
                winding_before=winding_before,
                winding_after=winding_after,
                closed=closed,
            )
        )
    return contributions

def winding_number(point: PointLike, polygon: list[PointLike], closed: bool = True) -> float:
    """
    point: the mean point. 
    Compute the winding number with respecto to this point
    """
    if not polygon:
        return 0.0

    # point center
    x, y = point_xy(point)
    
    wn = 0.0
    n = len(polygon)
    
    # for all edge of the polygon
    for i in range(n):
        # connect last point if closed
        if i == n - 1:
            if not closed:
                break
            next_idx = 0
        else:
            next_idx = i + 1
            
        p1_x, p1_y = point_xy(polygon[i])
        p2_x, p2_y = point_xy(polygon[next_idx])

        if closed:
            # wrt orizontal line
            if p1_y <= y:
                if p2_y > y:  # go up
                    # orientation test
                    if (p2_x - p1_x) * (y - p1_y) - (x - p1_x) * (p2_y - p1_y) > 0:
                        wn += 1.0
            else:
                if p2_y <= y:  # go down
                    # Orientation test
                    if (p2_x - p1_x) * (y - p1_y) - (x - p1_x) * (p2_y - p1_y) < 0:
                        wn -= 1.0

        else:
            # open
            x1, y1 = p1_x - x, p1_y - y
            x2, y2 = p2_x - x, p2_y - y

            # do compmute angle
            cross = x1 * y2 - y1 * x2
            dot = x1 * x2 + y1 * y2

    if closed:
        return wn
    
    #ony for visualization
    angle = math.atan2(cross, dot)
    wn += angle

    return wn / (2*math.pi)


def winding_trace(
    point: PointLike,
    polygon: list[PointLike],
    closed: bool = True,
) -> list[dict[str, object]]:
    steps: list[dict[str, object]] = []
    for contribution in winding_contributions(point, polygon, closed=closed):
        steps.append(
            {
                "edge_index": contribution.edge_index,
                "start": contribution.start,
                "end": contribution.end,
                "start_translated": contribution.start_translated,
                "end_translated": contribution.end_translated,
                "query_point_original": contribution.query_point_original,
                "query_point_translated": contribution.query_point_translated,
                "polygon_center": contribution.polygon_center,
                "vector_start": contribution.vector_start,
                "vector_end": contribution.vector_end,
                "cross": contribution.cross,
                "dot": contribution.dot,
                "angle_radians": contribution.angle_radians,
                "angle": contribution.angle,
                "winding_before": contribution.winding_before,
                "winding_after": contribution.winding_after,
                "winding": contribution.winding_after,
                "closed": contribution.closed,
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
    resolution: int = 100,
    discrete: bool = False,
    closed: bool = True,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    min_x, max_x, min_y, max_y = bounds
    xs = np.linspace(min_x, max_x, resolution)
    ys = np.linspace(min_y, max_y, resolution)
    field = np.zeros((resolution, resolution))

    setup = translated_winding_setup((0.0, 0.0), polygon)
    cx, cy = setup["polygon_center"]
    translated_polygon = setup["polygon_translated"]

    for row, y in enumerate(ys):
        for column, x in enumerate(xs):
            target_point = (x - cx, y - cy)
            winding = winding_number(target_point, translated_polygon, closed=closed)
            field[row, column] = 1.0 if discrete and abs(winding) > 0.5 else winding

    return field, xs, ys
