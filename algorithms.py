from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import math


Point = tuple[float, float]
Triangle = tuple[Point, Point, Point]
Grid = list[list[int]]
Segment = tuple[Point, Point]


@dataclass
class HullStep:
    action: str
    point: Point
    stack: list[Point]


@dataclass
class WindingStep:
    edge: Segment
    total_angle: float


@dataclass
class DelaunayStep:
    inserted_point: Point
    bad_triangles: list[Triangle]
    triangles: list[Triangle]


def signed_area(polygon: list[Point]) -> float:
    total = 0.0
    for index in range(len(polygon)):
        x1, y1 = polygon[index]
        x2, y2 = polygon[(index + 1) % len(polygon)]
        total += x1 * y2 - y1 * x2
    return total / 2.0


def ensure_counter_clockwise(polygon: list[Point]) -> list[Point]:
    if signed_area(polygon) < 0:
        return list(reversed(polygon))
    return polygon[:]


def orientation(a: Point, b: Point, c: Point) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def distance_squared(a: Point, b: Point) -> float:
    dx = a[0] - b[0]
    dy = a[1] - b[1]
    return dx * dx + dy * dy


def point_angle(anchor: Point, point: Point) -> float:
    return math.atan2(point[1] - anchor[1], point[0] - anchor[0])


def graham_scan(points: list[Point]) -> tuple[list[Point], list[HullStep]]:
    unique_points = sorted(set(points))
    if len(unique_points) <= 1:
        steps = [HullStep("seed", point, [point]) for point in unique_points]
        return unique_points, steps

    anchor = min(unique_points, key=lambda point: (point[1], point[0]))
    sorted_points = [anchor] + sorted(
        [point for point in unique_points if point != anchor],
        key=lambda point: (point_angle(anchor, point), distance_squared(anchor, point)),
    )

    stack: list[Point] = []
    steps: list[HullStep] = []

    for point in sorted_points:
        # Remove the last hull point while we turn clockwise or stay collinear.
        while len(stack) >= 2 and orientation(stack[-2], stack[-1], point) <= 0:
            stack.pop()
            steps.append(HullStep("pop", point, stack[:]))
        stack.append(point)
        steps.append(HullStep("push", point, stack[:]))

    return stack, steps


def polygon_edges(polygon: list[Point], closed: bool = True) -> list[Segment]:
    if len(polygon) < 2:
        return []

    edges: list[Segment] = []
    limit = len(polygon) if closed else len(polygon) - 1
    for index in range(limit):
        start = polygon[index]
        end = polygon[(index + 1) % len(polygon)]
        edges.append((start, end))
    return edges


def winding_number(point: Point, polygon: list[Point], closed: bool = True) -> float:
    total_angle = 0.0
    for start, end in polygon_edges(polygon, closed=closed):
        x1 = start[0] - point[0]
        y1 = start[1] - point[1]
        x2 = end[0] - point[0]
        y2 = end[1] - point[1]
        cross = x1 * y2 - y1 * x2
        dot = x1 * x2 + y1 * y2
        total_angle += math.atan2(cross, dot)
    return total_angle / (2.0 * math.pi)


def winding_steps(point: Point, polygon: list[Point], closed: bool = True) -> list[WindingStep]:
    total_angle = 0.0
    steps: list[WindingStep] = []
    for start, end in polygon_edges(polygon, closed=closed):
        x1 = start[0] - point[0]
        y1 = start[1] - point[1]
        x2 = end[0] - point[0]
        y2 = end[1] - point[1]
        total_angle += math.atan2(x1 * y2 - y1 * x2, x1 * x2 + y1 * y2)
        steps.append(WindingStep((start, end), total_angle / (2.0 * math.pi)))
    return steps


def point_in_polygon(point: Point, polygon: list[Point], closed: bool = True) -> bool:
    return abs(winding_number(point, polygon, closed=closed)) > 0.5


def polygon_bounds(polygons: list[list[Point]], padding: float = 1.0) -> tuple[float, float, float, float]:
    all_x = [point[0] for polygon in polygons for point in polygon]
    all_y = [point[1] for polygon in polygons for point in polygon]
    return (
        min(all_x) - padding,
        max(all_x) + padding,
        min(all_y) - padding,
        max(all_y) + padding,
    )


def sample_grid_points(
    bounds: tuple[float, float, float, float],
    rows: int,
    cols: int,
) -> tuple[list[float], list[float]]:
    min_x, max_x, min_y, max_y = bounds
    dx = (max_x - min_x) / cols
    dy = (max_y - min_y) / rows
    xs = [min_x + (column + 0.5) * dx for column in range(cols)]
    ys = [min_y + (row + 0.5) * dy for row in range(rows)]
    return xs, ys


def rasterize_polygon(
    polygon: list[Point],
    bounds: tuple[float, float, float, float],
    rows: int,
    cols: int,
    closed: bool = True,
) -> tuple[Grid, list[list[float]], tuple[list[float], list[float]]]:
    xs, ys = sample_grid_points(bounds, rows, cols)
    binary_grid: Grid = []
    winding_grid: list[list[float]] = []

    for y in ys:
        binary_row: list[int] = []
        winding_row: list[float] = []
        for x in xs:
            # Sample each cell at its center and keep both the continuous
            # winding value and the binary inside/outside decision.
            winding = winding_number((x, y), polygon, closed=closed)
            winding_row.append(winding)
            binary_row.append(1 if abs(winding) > 0.5 else 0)
        winding_grid.append(winding_row)
        binary_grid.append(binary_row)

    return binary_grid, winding_grid, (xs, ys)


def grid_union(grid_a: Grid, grid_b: Grid) -> Grid:
    return [
        [1 if cell_a or cell_b else 0 for cell_a, cell_b in zip(row_a, row_b)]
        for row_a, row_b in zip(grid_a, grid_b)
    ]


def grid_intersection(grid_a: Grid, grid_b: Grid) -> Grid:
    return [
        [1 if cell_a and cell_b else 0 for cell_a, cell_b in zip(row_a, row_b)]
        for row_a, row_b in zip(grid_a, grid_b)
    ]


def grid_difference(grid_a: Grid, grid_b: Grid) -> Grid:
    return [
        [1 if cell_a and not cell_b else 0 for cell_a, cell_b in zip(row_a, row_b)]
        for row_a, row_b in zip(grid_a, grid_b)
    ]


MARCHING_CASES: dict[int, list[tuple[Point, Point]]] = {
    0: [],
    1: [((0.0, 0.5), (0.5, 0.0))],
    2: [((0.5, 0.0), (1.0, 0.5))],
    3: [((0.0, 0.5), (1.0, 0.5))],
    4: [((1.0, 0.5), (0.5, 1.0))],
    5: [((0.0, 0.5), (0.5, 1.0)), ((0.5, 0.0), (1.0, 0.5))],
    6: [((0.5, 0.0), (0.5, 1.0))],
    7: [((0.0, 0.5), (0.5, 1.0))],
    8: [((0.5, 1.0), (0.0, 0.5))],
    9: [((0.5, 0.0), (0.5, 1.0))],
    10: [((0.0, 0.5), (0.5, 0.0)), ((0.5, 1.0), (1.0, 0.5))],
    11: [((1.0, 0.5), (0.5, 1.0))],
    12: [((0.0, 0.5), (1.0, 0.5))],
    13: [((0.5, 0.0), (1.0, 0.5))],
    14: [((0.0, 0.5), (0.5, 0.0))],
    15: [],
}


def marching_squares(
    grid: Grid,
    bounds: tuple[float, float, float, float],
) -> tuple[list[Segment], list[dict[str, object]]]:
    min_x, max_x, min_y, max_y = bounds
    rows = len(grid)
    cols = len(grid[0])
    dx = (max_x - min_x) / cols
    dy = (max_y - min_y) / rows
    segments: list[Segment] = []
    cells: list[dict[str, object]] = []

    # Each 2x2 block of samples becomes one case in the lookup table.
    for row in range(rows - 1):
        for column in range(cols - 1):
            # The 4 samples of the current cell are encoded as one 4-bit case.
            case_index = (
                grid[row][column] * 1
                + grid[row][column + 1] * 2
                + grid[row + 1][column + 1] * 4
                + grid[row + 1][column] * 8
            )

            cell_segments: list[Segment] = []
            for start, end in MARCHING_CASES[case_index]:
                world_start = (min_x + (column + start[0]) * dx, min_y + (row + start[1]) * dy)
                world_end = (min_x + (column + end[0]) * dx, min_y + (row + end[1]) * dy)
                segment = (world_start, world_end)
                segments.append(segment)
                cell_segments.append(segment)

            cells.append(
                {
                    "row": row,
                    "column": column,
                    "case_index": case_index,
                    "segments": cell_segments,
                }
            )

    return segments, cells


def round_point(point: Point, digits: int = 6) -> Point:
    return (round(point[0], digits), round(point[1], digits))


def stitch_segments(segments: list[Segment]) -> list[list[Point]]:
    adjacency: dict[Point, list[Point]] = defaultdict(list)
    for start, end in segments:
        rounded_start = round_point(start)
        rounded_end = round_point(end)
        adjacency[rounded_start].append(rounded_end)
        adjacency[rounded_end].append(rounded_start)

    visited_edges: set[tuple[Point, Point]] = set()
    polylines: list[list[Point]] = []

    for start, neighbors in adjacency.items():
        for next_point in neighbors:
            edge_key = tuple(sorted((start, next_point)))
            if edge_key in visited_edges:
                continue

            polyline = [start]
            current = start
            previous: Point | None = None

            while True:
                # Walk along unused incident edges until the contour closes
                # or reaches an open end.
                candidates = adjacency[current]
                next_candidate: Point | None = None
                for candidate in candidates:
                    candidate_key = tuple(sorted((current, candidate)))
                    if candidate_key in visited_edges:
                        continue
                    if previous is not None and candidate == previous and len(candidates) > 1:
                        continue
                    next_candidate = candidate
                    break

                if next_candidate is None:
                    break

                visited_edges.add(tuple(sorted((current, next_candidate))))
                polyline.append(next_candidate)
                previous, current = current, next_candidate

                if current == polyline[0]:
                    break

            if len(polyline) > 1:
                polylines.append(polyline)

    return polylines


def nearest_neighbor_path(polylines: list[list[Point]]) -> tuple[list[list[Point]], list[Segment]]:
    if not polylines:
        return [], []

    remaining = [line[:] for line in polylines]
    ordered = [remaining.pop(0)]
    travel_moves: list[Segment] = []

    while remaining:
        current_end = ordered[-1][-1]
        best_index = 0
        best_reverse = False
        best_distance = math.inf

        for index, polyline in enumerate(remaining):
            start_distance = distance_squared(current_end, polyline[0])
            end_distance = distance_squared(current_end, polyline[-1])
            if start_distance < best_distance:
                best_distance = start_distance
                best_index = index
                best_reverse = False
            if end_distance < best_distance:
                best_distance = end_distance
                best_index = index
                best_reverse = True

        chosen = remaining.pop(best_index)
        if best_reverse:
            chosen = list(reversed(chosen))

        travel_moves.append((current_end, chosen[0]))
        ordered.append(chosen)

    return ordered, travel_moves


def circumcircle_contains(triangle: Triangle, point: Point) -> bool:
    (ax, ay), (bx, by), (cx, cy) = triangle
    px, py = point

    ax -= px
    ay -= py
    bx -= px
    by -= py
    cx -= px
    cy -= py

    determinant = (
        (ax * ax + ay * ay) * (bx * cy - by * cx)
        - (bx * bx + by * by) * (ax * cy - ay * cx)
        + (cx * cx + cy * cy) * (ax * by - ay * bx)
    )
    return determinant > 1e-9


def canonical_triangle(a: Point, b: Point, c: Point) -> Triangle:
    triangle = [a, b, c]
    if orientation(a, b, c) < 0:
        triangle[1], triangle[2] = triangle[2], triangle[1]
    return triangle[0], triangle[1], triangle[2]


def super_triangle(points: list[Point]) -> Triangle:
    min_x = min(point[0] for point in points)
    max_x = max(point[0] for point in points)
    min_y = min(point[1] for point in points)
    max_y = max(point[1] for point in points)
    span = max(max_x - min_x, max_y - min_y)
    center_x = (min_x + max_x) / 2.0
    center_y = (min_y + max_y) / 2.0
    return (
        (center_x - 3.0 * span, center_y - span),
        (center_x, center_y + 3.0 * span),
        (center_x + 3.0 * span, center_y - span),
    )


def bowyer_watson(points: list[Point]) -> tuple[list[Triangle], list[DelaunayStep]]:
    ordered_points = sorted(set(points))
    if len(ordered_points) < 3:
        return [], []

    outer = canonical_triangle(*super_triangle(ordered_points))
    triangles: list[Triangle] = [outer]
    steps: list[DelaunayStep] = []

    for point in ordered_points:
        bad_triangles = [triangle for triangle in triangles if circumcircle_contains(triangle, point)]
        edge_counter: Counter[tuple[Point, Point]] = Counter()

        # Boundary edges appear once; inner edges appear twice and cancel out.
        for triangle in bad_triangles:
            for edge in ((triangle[0], triangle[1]), (triangle[1], triangle[2]), (triangle[2], triangle[0])):
                edge_counter[tuple(sorted(edge))] += 1

        triangles = [triangle for triangle in triangles if triangle not in bad_triangles]
        boundary_edges = [edge for edge, count in edge_counter.items() if count == 1]

        for start, end in boundary_edges:
            new_triangle = canonical_triangle(start, end, point)
            if abs(orientation(*new_triangle)) > 1e-9:
                triangles.append(new_triangle)

        steps.append(DelaunayStep(point, bad_triangles[:], triangles[:]))

    outer_points = set(outer)
    final_triangles = [
        triangle for triangle in triangles if not any(vertex in outer_points for vertex in triangle)
    ]
    return final_triangles, steps


def triangle_centroid(triangle: Triangle) -> Point:
    return (
        (triangle[0][0] + triangle[1][0] + triangle[2][0]) / 3.0,
        (triangle[0][1] + triangle[1][1] + triangle[2][1]) / 3.0,
    )


def prune_triangles_to_polygon(triangles: list[Triangle], polygon: list[Point]) -> list[Triangle]:
    kept: list[Triangle] = []
    for triangle in triangles:
        if point_in_polygon(triangle_centroid(triangle), polygon, closed=True):
            kept.append(triangle)
    return kept
