from __future__ import annotations

from dataclasses import dataclass
import math


PointTuple = tuple[float, float]


@dataclass
class HullSnapshot:
    pivot: PointTuple
    sorted_points: list[PointTuple]
    action: str
    candidate: PointTuple
    stack: list[PointTuple]


def orientation(a: PointTuple, b: PointTuple, c: PointTuple) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def graham_scan(points: list[PointTuple]) -> tuple[list[PointTuple], list[HullSnapshot]]:
    unique_points = sorted(set(points))
    if len(unique_points) < 3:
        return unique_points[:], [HullSnapshot(point, unique_points[:], "seed", point, [point]) for point in unique_points]

    pivot = min(unique_points, key=lambda point: (point[1], point[0]))

    def polar_angle(point: PointTuple) -> float:
        return math.atan2(point[1] - pivot[1], point[0] - pivot[0])

    sorted_points = [pivot] + sorted(
        (point for point in unique_points if point != pivot),
        key=lambda point: (polar_angle(point), math.dist(pivot, point)),
    )

    stack: list[PointTuple] = []
    snapshots: list[HullSnapshot] = []

    for point in sorted_points:
        # Remove the last point while the hull would turn clockwise or stay flat.
        while len(stack) >= 2 and orientation(stack[-2], stack[-1], point) <= 0:
            stack.pop()
            snapshots.append(HullSnapshot(pivot, sorted_points[:], "pop", point, stack[:]))
        stack.append(point)
        snapshots.append(HullSnapshot(pivot, sorted_points[:], "push", point, stack[:]))

    return stack, snapshots
